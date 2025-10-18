"""Figure generation utilities using processed SaveEcoBot datasets."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Optional, Set

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
import seaborn as sns

from src.lib import (
    MIN_COVERAGE_RATIO,
    MIN_PREWAR_YEARS,
    MIN_TOTAL_YEARS,
    MIN_WARTIME_YEARS,
    eligible_city_ids_from_daily,
    eligible_city_ids_from_distributions,
)

sns.set_theme(style="whitegrid", context="talk")
PRIMARY_COLORS = {"pre_war": "#1f78b4", "wartime": "#e31a1c"}
FIGSIZE_WIDE = (12, 6.75)
FIGSIZE_TALL = (10, 7.0)


def _ensure_period_order(periods: Iterable[str]) -> List[str]:
    order = ["pre_war", "wartime"]
    return [p for p in order if p in set(periods)]


def _despine_axes(ax_list: Iterable[plt.Axes]) -> None:
    for ax in ax_list:
        sns.despine(ax=ax)


def plot_distribution_shift(
    data: pd.DataFrame,
    output: Path,
    eligible_ids: Optional[Set[int]] = None,
) -> None:
    """Compare distribution of daily mean PM2.5 between pre-war and wartime."""
    df = data.dropna(subset=["pm25_mean", "period"]).copy()
    if eligible_ids:
        df = df[df["city_id"].isin(eligible_ids)]
    df = df[df["period"].isin(["pre_war", "wartime"])]
    if df.empty:
        raise ValueError("No daily PM2.5 data available for distribution plot")

    x_cap = df["pm25_mean"].quantile(0.995)
    x_max = float(min(120, x_cap * 1.05)) if np.isfinite(x_cap) else 120

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    sns.kdeplot(
        data=df,
        x="pm25_mean",
        hue="period",
        fill=True,
        common_norm=False,
        palette=PRIMARY_COLORS,
        linewidth=1.2,
        alpha=0.7,
        ax=ax,
    )
    ax.axvline(15, color="#444444", linestyle="--", linewidth=1, label="WHO guideline")
    ax.set(
        xlabel="Daily mean PM2.5 (µg/m³)",
        ylabel="Density",
        title="Distribution shift of daily mean PM2.5",
    )
    ax.set_xlim(0, max(40, x_max))
    ax.legend(frameon=False)
    fig.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.97)
    _despine_axes([ax])
    save_figure(fig, output)


def plot_city_ranking(
    data: pd.DataFrame,
    output: Path,
    top_n: int = 20,
    eligible_ids: Optional[Set[int]] = None,
) -> None:
    """Render a dumbbell chart ranking cities by median PM2.5 pre- vs wartime."""
    if eligible_ids is None:
        eligible_ids = eligible_city_ids_from_distributions(data)

    period = data[data["aggregation_level"] == "period"].copy()
    if eligible_ids:
        period = period[period["city_id"].isin(eligible_ids)]
    period = period[period["period"].isin(["pre_war", "wartime"])]
    period = period.assign(
        coverage_ratio=np.where(
            period["days"] > 0,
            period["days_with_coverage_ge18"] / period["days"],
            np.nan,
        )
    )
    period = (
        period.groupby(["city_id", "city_name", "period"], as_index=False)["pm25_median"].mean()
    )
    coverage = (
        data[data["aggregation_level"] == "period"]
        .assign(
            coverage_ratio=lambda df: np.where(
                df["days"] > 0,
                df["days_with_coverage_ge18"] / df["days"],
                np.nan,
            )
        )
        .pivot(index="city_id", columns="period", values="coverage_ratio")
    )

    pivot = period.pivot(index="city_id", columns="period", values="pm25_median")
    names = period.drop_duplicates("city_id").set_index("city_id")["city_name"]
    pivot = pivot.join(names)
    pivot = pivot.join(coverage.add_suffix("_coverage"))
    pivot = pivot.dropna(subset=["wartime"])
    pivot = pivot[
        (pivot.get("wartime_coverage", 0) >= 0.7)
        & (pivot.get("pre_war_coverage", 0) >= 0.7)
    ]
    if pivot.empty:
        raise ValueError("City distribution data missing for ranking plot")

    pivot = pivot.sort_values("wartime", ascending=False).head(top_n)
    cities = pivot["city_name"].tolist()[::-1]

    height = max(4.0, 0.45 * len(cities) + 3.0)
    fig, ax = plt.subplots(figsize=(FIGSIZE_WIDE[0], height))
    for city in cities:
        row = pivot[pivot["city_name"] == city].iloc[0]
        pre_val = row.get("pre_war")
        war_val = row.get("wartime")
        if pd.notna(pre_val) and pd.notna(war_val):
            ax.plot([pre_val, war_val], [city, city], color="#bbbbbb", linewidth=1.0)
        if pd.notna(pre_val):
            ax.scatter(pre_val, city, color=PRIMARY_COLORS["pre_war"], s=30, zorder=3)
        if pd.notna(war_val):
            ax.scatter(war_val, city, color=PRIMARY_COLORS["wartime"], s=30, zorder=3)

    ax.set(
        xlabel="Median daily PM2.5 (µg/m³)",
        ylabel="",
        title="City median PM2.5 — pre-war vs wartime",
    )
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.tick_params(axis="x", labelsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(
        handles=[
            plt.Line2D([0], [0], marker="o", color="w", label="Pre-war", markerfacecolor=PRIMARY_COLORS["pre_war"], markersize=8),
            plt.Line2D([0], [0], marker="o", color="w", label="Wartime", markerfacecolor=PRIMARY_COLORS["wartime"], markersize=8),
        ],
        frameon=False,
        loc="lower right",
    )
    fig.subplots_adjust(top=0.88, bottom=0.2, left=0.25, right=0.95)
    _despine_axes([ax])
    save_figure(fig, output)


def plot_inequality_panel(
    data: pd.DataFrame,
    output: Path,
    n_cities: int = 6,
    eligible_ids: Optional[Set[int]] = None,
) -> None:
    """Show yearly PM2.5 median and spread (p90/p10) for key cities."""
    if eligible_ids is None:
        eligible_ids = eligible_city_ids_from_distributions(data)

    period = data[data["aggregation_level"] == "period"].copy()
    period = period.assign(
        coverage_ratio=np.where(
            period["days"] > 0,
            period["days_with_coverage_ge18"] / period["days"],
            np.nan,
        )
    )
    wartime = period[(period["period"] == "wartime") & (period["coverage_ratio"] >= MIN_COVERAGE_RATIO)]
    if eligible_ids:
        wartime = wartime[wartime["city_id"].isin(eligible_ids)]
    top_cities = (
        wartime.sort_values("pm25_median", ascending=False)["city_name"].head(n_cities).tolist()
    )

    yearly = data[data["aggregation_level"] == "year"].copy()
    yearly = yearly[yearly["city_name"].isin(top_cities)]
    if yearly.empty:
        raise ValueError("Yearly distribution data missing for inequality panel")

    fig, axes = plt.subplots(
        2,
        int(np.ceil(n_cities / 2)),
        figsize=(FIGSIZE_WIDE[0], FIGSIZE_WIDE[1]),
        sharex=True,
        sharey=True,
    )
    axes = axes.flatten()

    for ax, city in zip(axes, top_cities):
        subset = yearly[yearly["city_name"] == city].sort_values("year")
        ax.fill_between(
            subset["year"],
            subset["pm25_p10"],
            subset["pm25_p90"],
            color="#c6dbef",
            alpha=0.7,
            label="p10–p90",
        )
        ax.plot(subset["year"], subset["pm25_median"], color="#08519c", linewidth=1.5, label="Median")
        if subset["year"].max() >= 2022:
            ax.axvspan(2022 - 0.5, subset["year"].max() + 0.5, color="#fee0d2", alpha=0.4)
        ax.set_title(city)
        ax.set_xlabel("Year")
        ax.set_ylabel("PM2.5 (µg/m³)")
        ax.grid(alpha=0.2)

    # Hide unused axes if n_cities is odd.
    for ax in axes[len(top_cities) :]:
        ax.set_visible(False)

    handles = [
        plt.Line2D([0], [0], color="#08519c", label="Median"),
        plt.Line2D([0], [0], color="#c6dbef", linewidth=6, alpha=0.7, label="p10–p90"),
    ]
    fig.suptitle("Yearly PM2.5 spread for high-pollution cities", y=0.97)
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=2,
        frameon=False,
    )
    fig.subplots_adjust(top=0.88, bottom=0.12, left=0.07, right=0.98, hspace=0.3)
    _despine_axes(ax for ax in axes if ax.get_visible())
    save_figure(fig, output)


def plot_heatmap(data: pd.DataFrame, output: Path) -> None:
    """Render hour×month heatmaps for pre-war and wartime periods."""
    frame = data.copy()
    if "is_valid" in frame.columns:
        frame = frame[frame["is_valid"]]
    if "period" not in frame.columns:
        frame["period"] = np.where(frame["is_wartime"], "wartime", "pre_war")

    grouped = (
        frame.groupby(["period", "month", "hour_local"], dropna=False)["pm25"].mean().reset_index()
    )
    periods = _ensure_period_order(grouped["period"].unique())
    if not periods:
        raise ValueError("Hourly dataset missing period information for heatmap")

    fig, axes = plt.subplots(1, len(periods), figsize=FIGSIZE_WIDE, sharey=True)
    if len(periods) == 1:
        axes = [axes]

    month_labels = ["Jan", "", "Mar", "", "May", "", "Jul", "", "Sep", "", "Nov", ""]
    vmax = grouped["pm25"].max()
    vmin = grouped["pm25"].min()

    for ax, period in zip(axes, periods):
        subset = grouped[grouped["period"] == period]
        pivot = subset.pivot(index="hour_local", columns="month", values="pm25")
        pivot = pivot.reindex(index=range(24), columns=range(1, 13))
        sns.heatmap(
            pivot,
            cmap="mako",
            ax=ax,
            cbar=ax is axes[-1],
            vmin=vmin,
            vmax=vmax,
        )
        ax.set_title(f"{period.replace('_', ' ').title()}")
        ax.set_xlabel("Month")
        ax.set_xticklabels(month_labels, rotation=45, ha="right")
        ax.set_ylabel("Local Hour")
        ax.set_yticks(range(0, 24, 3))

    fig.suptitle("Average hourly PM2.5 by month and hour", y=0.96)
    fig.subplots_adjust(top=0.88, bottom=0.12, left=0.08, right=0.98, wspace=0.12)
    _despine_axes(axes)
    save_figure(fig, output)


def plot_exceedance_timeline(
    data: pd.DataFrame,
    output: Path,
    cities: int = 4,
    eligible_ids: Optional[Set[int]] = None,
) -> None:
    """Plot rolling exceedance share for national average and key cities."""
    daily = data.copy()
    if eligible_ids:
        daily = daily[daily["city_id"].isin(eligible_ids)]
    daily = daily[daily["available_hours"] > 0]
    daily["coverage_share"] = daily["available_hours"] / 24.0

    if daily.empty:
        raise ValueError("Daily dataset empty; cannot create exceedance timeline")

    # Weighted national average by available hours.
    national = daily.groupby("date_local")[
        ["exceedance_hours", "available_hours"]
    ].sum().reset_index()
    national["exceedance_share"] = np.where(
        national["available_hours"] > 0,
        national["exceedance_hours"] / national["available_hours"],
        np.nan,
    )
    national["city_name"] = "National average"

    wartime_daily = daily[daily["period"] == "wartime"].copy()
    wartime_daily = wartime_daily.assign(coverage_flag=wartime_daily["available_hours"] >= 18)
    coverage_ratio = wartime_daily.groupby("city_name")["coverage_flag"].mean()
    coverage_ratio = coverage_ratio[coverage_ratio >= 0.7]
    exceed_means = wartime_daily.groupby("city_name")["exceedance_share"].mean()
    wartime_means = (
        exceed_means.reindex(coverage_ratio.index).dropna().sort_values(ascending=False).head(cities).index
    )
    top_cities = daily[daily["city_name"].isin(wartime_means)].copy()

    combined = pd.concat([national, top_cities], ignore_index=True)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    for name, group in combined.groupby("city_name"):
        group = group.sort_values("date_local")
        ax.plot(group["date_local"], group["exceedance_share"].rolling(30, min_periods=7).mean(), label=name)

    ax.axhline(0.25, color="#999999", linestyle="--", linewidth=0.8)
    ax.set(
        xlabel="Date",
        ylabel="Share of hours > 15 µg/m³ (30-day avg)",
        title="PM2.5 guideline exceedance over time",
    )
    ax.legend(frameon=False, ncol=2)
    ax.set_ylim(0, 1)
    fig.subplots_adjust(top=0.88, bottom=0.16, left=0.08, right=0.97)
    _despine_axes([ax])
    save_figure(fig, output)


def plot_station_coverage(
    data: pd.DataFrame,
    output: Path,
    cities: int = 10,
    eligible_ids: Optional[Set[int]] = None,
) -> None:
    """Approximate station coverage via available-hours share for top cities."""
    daily = data.copy()
    if eligible_ids:
        daily = daily[daily["city_id"].isin(eligible_ids)]
    daily["coverage"] = daily["available_hours"] / 24.0
    daily_monthly = (
        daily.groupby(["city_name", pd.Grouper(key="date_local", freq="MS")])
        .agg(coverage_mean=("coverage", "mean"))
        .reset_index()
    )
    wartime_cov = (
        daily_monthly[daily_monthly["date_local"] >= pd.Timestamp(2022, 1, 1)]
        .groupby("city_name")["coverage_mean"].mean().sort_values(ascending=False)
    )
    top_cities = wartime_cov.head(cities).index
    subset = daily_monthly[daily_monthly["city_name"].isin(top_cities)]
    if subset.empty:
        raise ValueError("Coverage data unavailable for station coverage plot")

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    sns.lineplot(
        data=subset,
        x="date_local",
        y="coverage_mean",
        hue="city_name",
        linewidth=1.5,
        ax=ax,
    )
    ax.set(
        xlabel="Month",
        ylabel="Average available hours / 24",
        title="Sensor coverage proxy by city",
    )
    ax.legend(title="City", frameon=False, ncol=2)
    ax.set_ylim(0, 1)
    fig.subplots_adjust(top=0.88, bottom=0.18, left=0.08, right=0.97)
    _despine_axes([ax])
    save_figure(fig, output)


def plot_aqi_pm25_scatter(
    data: pd.DataFrame,
    output: Path,
    sample: int = 200_000,
    eligible_ids: Optional[Set[int]] = None,
) -> None:
    """Plot AQI vs PM2.5 relationship using sampled hourly data."""
    frame = data.dropna(subset=["pm25", "aqi"]).copy()
    if "is_valid" in frame.columns:
        frame = frame[frame["is_valid"]]
    if eligible_ids:
        frame = frame[frame["city_id"].isin(eligible_ids)]
    if frame.empty:
        raise ValueError("Hourly dataset lacks valid PM2.5/AQI pairs")

    frame["period"] = np.where(frame["is_wartime"], "wartime", "pre_war")
    periods = _ensure_period_order(frame["period"].unique())

    fig, axes = plt.subplots(1, len(periods), figsize=FIGSIZE_WIDE, sharex=True, sharey=True)
    if len(periods) == 1:
        axes = [axes]

    for ax, period in zip(axes, periods):
        subset = frame[frame["period"] == period]
        if len(subset) > sample:
            subset = subset.sample(sample, random_state=42)
        ax.hexbin(subset["pm25"], subset["aqi"], gridsize=50, cmap="viridis", mincnt=1)
        ax.set(
            xlabel="PM2.5 (µg/m³)",
            ylabel="AQI",
            title=f"{period.replace('_', ' ').title()}"
        )
        ax.axvline(15, color="#ff7f00", linestyle="--", linewidth=1)
        ax.set_xlim(left=0)
        ax.set_ylim(0, 500)

    fig.suptitle("Relationship between PM2.5 and AQI", y=0.96)
    fig.subplots_adjust(top=0.88, bottom=0.14, left=0.08, right=0.97, wspace=0.12)
    _despine_axes(axes)
    save_figure(fig, output)


def plot_choropleth(geo_data: gpd.GeoDataFrame, output: Path) -> None:
    """Create a split-panel choropleth of average PM2.5 by region."""
    if geo_data.empty:
        raise ValueError("Region-level dataset empty; cannot create choropleth")

    periods = _ensure_period_order(geo_data["period"].unique())
    fig, axes = plt.subplots(1, len(periods), figsize=FIGSIZE_WIDE)
    if len(periods) == 1:
        axes = [axes]

    cmap = plt.cm.get_cmap("YlOrRd")
    vmax = geo_data["pm25_median"].max()
    norm = plt.Normalize(vmin=0, vmax=vmax)
    for ax, period in zip(axes, periods):
        subset = geo_data[geo_data["period"] == period].copy()
        subset.plot(
            column="pm25_median",
            cmap=cmap,
            linewidth=0.2,
            edgecolor="#666666",
            vmin=norm.vmin,
            vmax=norm.vmax,
            ax=ax,
            legend=False,
            missing_kwds={"color": "#e0e0e0", "edgecolor": "#c0c0c0"},
        )
        ax.set_title(period.replace("_", " ").title())
        ax.axis("off")

    fig.suptitle("Regional median PM2.5", y=0.96)
    fig.subplots_adjust(top=0.88, bottom=0.05, left=0.03, right=0.95, wspace=0.04)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm._A = []
    fig.colorbar(sm, ax=list(axes), fraction=0.025, pad=0.015, label="Median PM2.5 (µg/m³)")
    _despine_axes(axes)
    save_figure(fig, output)


def save_figure(fig: Any, output: Path) -> None:
    """Standardized export helper for PNG/SVG outputs."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
