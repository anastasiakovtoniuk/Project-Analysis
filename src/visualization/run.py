"""CLI for generating publication-ready figures."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import geopandas as gpd
import pandas as pd
import typer

from .figures import (
    plot_aqi_pm25_scatter,
    plot_choropleth,
    plot_city_ranking,
    plot_distribution_shift,
    plot_exceedance_timeline,
    plot_heatmap,
    plot_inequality_panel,
    plot_station_coverage,
)
from src.lib import eligible_city_ids_from_distributions

app = typer.Typer(help="Render analytical figures from processed datasets.")


def _resolve(path: Path) -> Path:
    return path.expanduser().resolve()


def _load_processed(processed_dir: Path) -> Dict[str, pd.DataFrame]:
    processed_dir = _resolve(processed_dir)
    hourly_path = processed_dir / "city_hourly_pm25.parquet"
    daily_path = processed_dir / "city_daily_pm25.parquet"
    distributions_path = processed_dir / "city_distributions.parquet"
    region_path = processed_dir / "region_period_pm25.parquet"

    if not hourly_path.exists():
        raise FileNotFoundError(f"Missing hourly parquet: {hourly_path}")
    if not daily_path.exists():
        raise FileNotFoundError(f"Missing daily parquet: {daily_path}")
    if not distributions_path.exists():
        raise FileNotFoundError(f"Missing city distributions parquet: {distributions_path}")
    if not region_path.exists():
        raise FileNotFoundError(f"Missing region parquet: {region_path}")

    hourly = pd.read_parquet(hourly_path)
    daily = pd.read_parquet(daily_path)
    distributions = pd.read_parquet(distributions_path)
    region = gpd.read_parquet(region_path)

    return {
        "hourly": hourly,
        "daily": daily,
        "distributions": distributions,
        "region": region,
    }


def _output_dir(figures_dir: Path) -> Path:
    path = _resolve(figures_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@app.command()
def all(
    processed_dir: Path = typer.Option(Path("data/processed"), help="Directory with processed parquet files."),
    figures_dir: Path = typer.Option(Path("outputs/figures"), help="Directory to write figures."),
) -> None:
    """Render all figures using default parameters."""
    data = _load_processed(processed_dir)
    out_dir = _output_dir(figures_dir)

    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])

    plot_distribution_shift(
        data["daily"], out_dir / "01_distribution_shift.png", eligible_ids=eligible_ids
    )
    plot_city_ranking(
        data["distributions"],
        out_dir / "02_city_median_ranking.png",
        eligible_ids=eligible_ids,
    )
    plot_inequality_panel(
        data["distributions"],
        out_dir / "03_city_inequality_panel.png",
        eligible_ids=eligible_ids,
    )
    plot_heatmap(data["hourly"], out_dir / "04_seasonal_heatmap.png")
    plot_exceedance_timeline(
        data["daily"],
        out_dir / "05_exceedance_timeline.png",
        eligible_ids=eligible_ids,
    )
    plot_station_coverage(
        data["daily"],
        out_dir / "06_station_coverage.png",
        eligible_ids=eligible_ids,
    )
    plot_aqi_pm25_scatter(
        data["hourly"],
        out_dir / "07_aqi_pm25_scatter.png",
        eligible_ids=eligible_ids,
    )
    plot_choropleth(data["region"], out_dir / "08_choropleth.png")
    typer.secho("All figures exported", fg=typer.colors.GREEN)


@app.command()
def distribution(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
) -> None:
    """Render only the distribution shift figure."""
    data = _load_processed(processed_dir)
    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])
    plot_distribution_shift(
        data["daily"],
        _output_dir(figures_dir) / "01_distribution_shift.png",
        eligible_ids=eligible_ids,
    )


@app.command()
def ranking(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
    top_n: int = typer.Option(20, help="Number of cities to display."),
) -> None:
    data = _load_processed(processed_dir)
    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])
    plot_city_ranking(
        data["distributions"],
        _output_dir(figures_dir) / "02_city_median_ranking.png",
        top_n=top_n,
        eligible_ids=eligible_ids,
    )


@app.command()
def inequality(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
    n_cities: int = typer.Option(6, help="Number of cities to include."),
) -> None:
    data = _load_processed(processed_dir)
    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])
    plot_inequality_panel(
        data["distributions"],
        _output_dir(figures_dir) / "03_city_inequality_panel.png",
        n_cities=n_cities,
        eligible_ids=eligible_ids,
    )


@app.command()
def heatmap(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
) -> None:
    data = _load_processed(processed_dir)
    plot_heatmap(data["hourly"], _output_dir(figures_dir) / "04_seasonal_heatmap.png")


@app.command()
def exceedance(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
    cities: int = typer.Option(4, help="Number of individual cities to highlight."),
) -> None:
    data = _load_processed(processed_dir)
    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])
    plot_exceedance_timeline(
        data["daily"],
        _output_dir(figures_dir) / "05_exceedance_timeline.png",
        cities=cities,
        eligible_ids=eligible_ids,
    )


@app.command()
def coverage(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
    cities: int = typer.Option(10, help="Number of cities to track."),
) -> None:
    data = _load_processed(processed_dir)
    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])
    plot_station_coverage(
        data["daily"],
        _output_dir(figures_dir) / "06_station_coverage.png",
        cities=cities,
        eligible_ids=eligible_ids,
    )


@app.command()
def scatter(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
    sample: int = typer.Option(200_000, help="Samples per period."),
) -> None:
    data = _load_processed(processed_dir)
    eligible_ids = eligible_city_ids_from_distributions(data["distributions"])
    plot_aqi_pm25_scatter(
        data["hourly"],
        _output_dir(figures_dir) / "07_aqi_pm25_scatter.png",
        sample=sample,
        eligible_ids=eligible_ids,
    )


@app.command()
def choropleth(
    processed_dir: Path = typer.Option(Path("data/processed")),
    figures_dir: Path = typer.Option(Path("outputs/figures")),
) -> None:
    data = _load_processed(processed_dir)
    plot_choropleth(data["region"], _output_dir(figures_dir) / "08_choropleth.png")


if __name__ == "__main__":
    app()
