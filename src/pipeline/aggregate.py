"""Aggregation utilities for SaveEcoBot hourly PM2.5 data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

from src.lib import eligible_city_year_pairs_from_daily


@dataclass
class AggregationResult:
    """Summary of artefacts produced by aggregation."""

    hourly_rows: int
    daily_rows: int
    city_distribution_rows: int
    region_period_rows: int
    eligible_cities: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "hourly_rows": self.hourly_rows,
            "daily_rows": self.daily_rows,
            "city_distribution_rows": self.city_distribution_rows,
            "region_period_rows": self.region_period_rows,
            "eligible_cities": self.eligible_cities,
        }


def _season_from_month(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def _load_hourly(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("city_hourly_*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found in {raw_dir}")
    frames = [pd.read_parquet(path) for path in files]
    hourly = pd.concat(frames, ignore_index=True)
    if "logged_at" not in hourly.columns:
        raise ValueError("Expected column 'logged_at' missing from hourly parquet")
    hourly["logged_at"] = pd.to_datetime(hourly["logged_at"], utc=True, errors="coerce")
    return hourly.dropna(subset=["logged_at", "city_id"])


def _prepare_metadata(cities_metadata: Path) -> pd.DataFrame:
    meta = pd.read_csv(cities_metadata)
    meta.columns = meta.columns.str.lower()
    if "id" not in meta.columns:
        raise ValueError("City metadata missing 'id' column")
    meta = meta.rename(columns={"id": "city_id"})
    return meta[["city_id", "city_name", "region_name", "koatuu", "katottg"]]


def _enrich_hourly(
    hourly: pd.DataFrame,
    meta: pd.DataFrame,
    timezone: str,
    wartime_start: date,
) -> pd.DataFrame:
    tzinfo = ZoneInfo(timezone)
    hourly = hourly.copy()
    hourly["logged_at_local"] = hourly["logged_at"].dt.tz_convert(tzinfo)
    hourly["date_local"] = hourly["logged_at_local"].dt.tz_localize(None).dt.normalize()
    hourly["hour_local"] = hourly["logged_at_local"].dt.hour
    hourly["month"] = hourly["logged_at_local"].dt.month
    hourly["year"] = hourly["logged_at_local"].dt.year
    hourly["weekday"] = hourly["logged_at_local"].dt.dayofweek
    hourly["weekofyear"] = hourly["logged_at_local"].dt.isocalendar().week.astype(int)
    hourly["season"] = hourly["month"].map(_season_from_month)

    wartime_start_ts = pd.Timestamp(wartime_start, tz=tzinfo)
    hourly["is_wartime"] = hourly["logged_at_local"] >= wartime_start_ts
    hourly["period"] = np.where(hourly["is_wartime"], "wartime", "pre_war")

    hourly = hourly.merge(meta, on="city_id", how="left")

    hourly["pm25_valid"] = hourly["pm25"].between(0, 1_000, inclusive="both") | hourly["pm25"].isna()
    hourly["aqi_valid"] = hourly["aqi"].between(0, 500, inclusive="both") | hourly["aqi"].isna()
    hourly["is_valid"] = hourly["pm25_valid"] & hourly["aqi_valid"]

    hourly["date_local"] = pd.to_datetime(hourly["date_local"], utc=False)

    return hourly


def _daily_aggregates(hourly: pd.DataFrame, pm25_guideline: float, wartime_start: date) -> pd.DataFrame:
    valid = hourly[hourly["is_valid"]].copy()
    if valid.empty:
        raise RuntimeError("No valid hourly records available for aggregation")

    valid["exceed"] = valid["pm25"] > pm25_guideline

    group_cols = ["city_id", "city_name", "region_name", "date_local"]
    daily = (
        valid.groupby(group_cols)
        .agg(
            pm25_mean=("pm25", "mean"),
            pm25_median=("pm25", "median"),
            pm25_p90=("pm25", lambda s: float(s.quantile(0.9))),
            pm25_p10=("pm25", lambda s: float(s.quantile(0.1))),
            pm25_max=("pm25", "max"),
            available_hours=("pm25", "size"),
            exceedance_hours=("exceed", "sum"),
            aqi_mean=("aqi", "mean"),
        )
        .reset_index()
    )

    daily["date_local"] = pd.to_datetime(daily["date_local"], utc=False)
    daily["exceedance_share"] = np.where(
        daily["available_hours"] > 0,
        daily["exceedance_hours"] / daily["available_hours"],
        np.nan,
    )
    daily["year"] = daily["date_local"].dt.year
    daily["month"] = daily["date_local"].dt.month
    daily["weekday"] = daily["date_local"].dt.dayofweek
    daily["season"] = daily["month"].map(_season_from_month)
    wartime_start_ts = pd.Timestamp(wartime_start)
    daily["is_wartime"] = daily["date_local"] >= wartime_start_ts
    daily["period"] = np.where(daily["is_wartime"], "wartime", "pre_war")

    return daily


def _city_distributions(daily: pd.DataFrame) -> pd.DataFrame:
    def _coverage(series: pd.Series) -> float:
        return float((series >= 18).sum())

    aggregations = {
        "days": ("date_local", "count"),
        "pm25_mean": ("pm25_mean", "mean"),
        "pm25_median": ("pm25_median", "median"),
        "pm25_p90": ("pm25_median", lambda s: float(s.quantile(0.9))),
        "pm25_p10": ("pm25_median", lambda s: float(s.quantile(0.1))),
        "exceedance_share": ("exceedance_share", "mean"),
        "available_hours_mean": ("available_hours", "mean"),
        "days_with_coverage_ge18": ("available_hours", _coverage),
    }

    period_summary = (
        daily.groupby(["city_id", "city_name", "region_name", "period"], dropna=False)
        .agg(**aggregations)
        .reset_index()
    )
    period_summary["aggregation_level"] = "period"

    year_summary = (
        daily.groupby(["city_id", "city_name", "region_name", "year"], dropna=False)
        .agg(**aggregations)
        .reset_index()
    )
    year_summary["aggregation_level"] = "year"

    distributions = pd.concat([period_summary, year_summary], ignore_index=True)
    return distributions


def _region_period_summary(daily: pd.DataFrame) -> pd.DataFrame:
    return (
        daily.groupby(["region_name", "period"], dropna=False)
        .agg(
            cities=("city_id", pd.Series.nunique),
            days=("date_local", "count"),
            pm25_mean=("pm25_mean", "mean"),
            pm25_median=("pm25_median", "median"),
            pm25_p90=("pm25_median", lambda s: float(s.quantile(0.9))),
            exceedance_share=("exceedance_share", "mean"),
        )
        .reset_index()
    )


def aggregate_data(
    raw_dir: Path,
    processed_dir: Path,
    cities_metadata: Path,
    admin_boundaries: Optional[Path],
    timezone: str,
    wartime_start: date,
    pm25_guideline: float,
) -> Dict[str, int]:
    """Run aggregation pipeline and persist outputs to processed_dir."""

    processed_dir.mkdir(parents=True, exist_ok=True)

    hourly = _load_hourly(raw_dir)
    meta = _prepare_metadata(cities_metadata)
    hourly_enriched = _enrich_hourly(hourly, meta, timezone, wartime_start)

    daily = _daily_aggregates(hourly_enriched, pm25_guideline, wartime_start)
    eligible_pairs = eligible_city_year_pairs_from_daily(daily)
    if not eligible_pairs:
        raise RuntimeError("No cities meet coverage criteria for analysis")

    eligible_pairs_df = pd.DataFrame(list(eligible_pairs), columns=["city_id", "year"])
    eligible_pairs_df["city_id"] = eligible_pairs_df["city_id"].astype(int)
    eligible_pairs_df["year"] = eligible_pairs_df["year"].astype(int)
    eligible_ids = set(eligible_pairs_df["city_id"].tolist())

    hourly_enriched = hourly_enriched.merge(eligible_pairs_df, on=["city_id", "year"], how="inner")
    daily = daily.merge(eligible_pairs_df, on=["city_id", "year"], how="inner")

    hourly_path = processed_dir / "city_hourly_pm25.parquet"
    hourly_enriched.to_parquet(hourly_path, index=False)
    daily_path = processed_dir / "city_daily_pm25.parquet"
    daily.to_parquet(daily_path, index=False)

    distributions = _city_distributions(daily)
    distributions_path = processed_dir / "city_distributions.parquet"
    distributions.to_parquet(distributions_path, index=False)

    region_period = _region_period_summary(daily)

    region_rows = len(region_period)
    if admin_boundaries and admin_boundaries.exists():
        admin = gpd.read_file(admin_boundaries)
        if "name:uk" in admin.columns:
            admin_name = admin["name:uk"].fillna("")
        elif "name" in admin.columns:
            admin_name = admin["name"].fillna("")
        else:
            raise ValueError("Administrative boundaries file missing name attributes for join")

        admin["region_key"] = admin_name.str.strip()
        region_period["region_key"] = region_period["region_name"].str.strip()
        merge_cols = ["region_key", "geometry"]
        if "koatuu" in admin.columns:
            merge_cols.append("koatuu")
        merged = region_period.merge(
            admin[merge_cols],
            how="left",
            on="region_key",
        )
        merged_gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs=admin.crs)
        merged_gdf = merged_gdf.drop(columns=["region_key"], errors="ignore")
        merged_gdf.to_parquet(processed_dir / "region_period_pm25.parquet", index=False)
        region_rows = len(merged_gdf)
    else:
        region_period.drop(columns=["region_key"], errors="ignore").to_parquet(
            processed_dir / "region_period_pm25.parquet", index=False
        )

    result = AggregationResult(
        hourly_rows=len(hourly_enriched),
        daily_rows=len(daily),
        city_distribution_rows=len(distributions),
        region_period_rows=region_rows,
        eligible_cities=len(eligible_ids),
    )

    return result.to_dict()


__all__ = ["aggregate_data"]
