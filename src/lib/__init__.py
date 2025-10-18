"""Shared utilities for the project."""

from .eligibility import (
    MIN_COVERAGE_RATIO,
    MIN_PREWAR_YEARS,
    MIN_TOTAL_YEARS,
    MIN_WARTIME_YEARS,
    eligible_city_ids_from_daily,
    eligible_city_ids_from_distributions,
    eligible_city_year_pairs_from_daily,
)

__all__ = [
    "MIN_COVERAGE_RATIO",
    "MIN_PREWAR_YEARS",
    "MIN_TOTAL_YEARS",
    "MIN_WARTIME_YEARS",
    "eligible_city_ids_from_daily",
    "eligible_city_ids_from_distributions",
    "eligible_city_year_pairs_from_daily",
]
