"""Eligibility filters for city-level analyses based on coverage."""
from __future__ import annotations

from typing import Set, Tuple

import numpy as np
import pandas as pd

MIN_COVERAGE_RATIO = 0.7
MIN_TOTAL_YEARS = 4
MIN_PREWAR_YEARS = 2
MIN_WARTIME_YEARS = 2


def _compute_good_years(df: pd.DataFrame) -> pd.DataFrame:
    coverage = (
        df.groupby(["city_id", "city_name", "year"], dropna=False)
        .agg(
            days=("date_local", "nunique"),
            coverage_days=("available_hours", lambda s: (s >= 18).sum()),
        )
        .reset_index()
    )
    coverage["coverage_ratio"] = np.where(
        coverage["days"] > 0,
        coverage["coverage_days"] / coverage["days"],
        0.0,
    )
    return coverage[coverage["coverage_ratio"] >= MIN_COVERAGE_RATIO]


def _eligible_city_ids(good_years: pd.DataFrame) -> Set[int]:
    total_counts = good_years.groupby("city_id")["year"].nunique()
    prewar_counts = good_years[good_years["year"] <= 2021].groupby("city_id")["year"].nunique()
    wartime_counts = good_years[good_years["year"] >= 2022].groupby("city_id")["year"].nunique()

    eligible: Set[int] = set()
    for city_id, total in total_counts.items():
        pre = prewar_counts.get(city_id, 0)
        war = wartime_counts.get(city_id, 0)
        if total >= MIN_TOTAL_YEARS and pre >= MIN_PREWAR_YEARS and war >= MIN_WARTIME_YEARS:
            eligible.add(int(city_id))
    return eligible


def eligible_city_year_pairs_from_daily(daily: pd.DataFrame) -> Set[Tuple[int, int]]:
    if daily.empty:
        return set()
    df = daily.copy()
    df["date_local"] = pd.to_datetime(df["date_local"], errors="coerce")
    df["year"] = df["date_local"].dt.year
    good_years = _compute_good_years(df)
    eligible_ids = _eligible_city_ids(good_years)
    filtered = good_years[good_years["city_id"].isin(eligible_ids)]
    return {(int(row.city_id), int(row.year)) for row in filtered.itertuples()}


def eligible_city_ids_from_daily(daily: pd.DataFrame) -> Set[int]:
    pairs = eligible_city_year_pairs_from_daily(daily)
    return {city_id for city_id, _ in pairs}


def eligible_city_ids_from_distributions(distributions: pd.DataFrame) -> Set[int]:
    year_level = distributions[
        distributions["aggregation_level"] == "year"
    ].dropna(subset=["year"]).copy()
    if year_level.empty:
        return set()
    year_level["year"] = year_level["year"].astype(int)
    year_level["date_local"] = pd.to_datetime(
        year_level["year"].astype(str) + "-01-01", errors="coerce"
    )
    good_years = year_level[year_level["days"] > 0].copy()
    good_years = good_years.assign(
        coverage_days=lambda df: df["days_with_coverage_ge18"],
    )
    good_years = good_years.rename(columns={"year": "year"})
    good_years = good_years[[
        "city_id",
        "city_name",
        "year",
        "days",
        "coverage_days",
    ]]
    good_years = good_years.assign(
        coverage_ratio=np.where(
            good_years["days"] > 0,
            good_years["coverage_days"] / good_years["days"],
            0.0,
        )
    )
    good_years = good_years[good_years["coverage_ratio"] >= MIN_COVERAGE_RATIO]
    return _eligible_city_ids(good_years)
