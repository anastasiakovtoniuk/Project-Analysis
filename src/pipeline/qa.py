"""QA utilities for processed SaveEcoBot datasets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


def _share_ge_threshold(series: pd.Series, threshold: float) -> float:
    if series.empty:
        return float("nan")
    return float((series >= threshold).sum() / len(series))


def run_qa(processed_dir: Path, qa_dir: Path, pm25_guideline: float) -> Dict[str, object]:
    qa_dir.mkdir(parents=True, exist_ok=True)

    daily_path = processed_dir / "city_daily_pm25.parquet"
    if not daily_path.exists():
        raise FileNotFoundError("Daily processed data not found. Run aggregate stage first.")

    daily = pd.read_parquet(daily_path)
    if daily.empty:
        raise RuntimeError("Daily dataset is empty; cannot compute QA metrics.")

    daily["date_local"] = pd.to_datetime(daily["date_local"], errors="coerce")

    coverage = (
        daily.groupby(["city_id", "city_name", "region_name", "year"], dropna=False)
        .agg(
            days_observed=("date_local", "count"),
            mean_available_hours=("available_hours", "mean"),
            median_available_hours=("available_hours", "median"),
            share_days_ge18=("available_hours", lambda s: _share_ge_threshold(s, 18)),
            mean_exceedance_share=("exceedance_share", "mean"),
        )
        .reset_index()
    )
    coverage.to_csv(qa_dir / "city_year_coverage.csv", index=False)

    period_summary = (
        daily.groupby("period")
        .agg(
            pm25_median=("pm25_median", "median"),
            exceedance_share=("exceedance_share", "mean"),
        )
        .reset_index()
    )
    period_summary.to_csv(qa_dir / "period_summary.csv", index=False)

    summary = {
        "cities": int(daily["city_id"].nunique()),
        "years": sorted(int(year) for year in daily["year"].dropna().unique()),
        "daily_rows": int(len(daily)),
        "pm25_guideline": pm25_guideline,
    }

    with (qa_dir / "qa_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


__all__ = ["run_qa"]
