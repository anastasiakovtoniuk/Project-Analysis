"""Command-line entry point for the data processing pipeline."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer

from .ingest import ingest_hourly
from .aggregate import aggregate_data
from .qa import run_qa

app = typer.Typer(help="Run data pipeline stages.")


def _resolve(path: Path) -> Path:
    """Return the absolute path for user-provided directories."""
    return path.expanduser().resolve()


@app.command()
def ingest(
    hourly_pattern: str = typer.Option(
        "dataset/saveecobot_cities_pm25_and_aqi_pm25_*.csv",
        help="Glob pattern for hourly CSV files.",
    ),
    cities_metadata: Path = typer.Option(
        Path("dataset/saveecobot_cities.csv"),
        help="Path to city metadata CSV.",
    ),
    raw_dir: Path = typer.Option(Path("data/raw"), help="Output directory for raw parquet files."),
    timezone: str = typer.Option("Europe/Kyiv", help="Timezone for localising timestamps."),
    year: Optional[int] = typer.Option(None, help="Restrict ingest to a single year."),
    archive_csv: Optional[Path] = typer.Option(
        None,
        help="Optional combined CSV to capture additional years (e.g., 2024+).",
    ),
) -> None:
    """Load hourly CSVs and store them as parquet files grouped by year."""
    stats = ingest_hourly(
        hourly_pattern,
        _resolve(cities_metadata),
        _resolve(raw_dir),
        timezone,
        year,
        archive_csv=_resolve(archive_csv) if archive_csv else None,
    )
    typer.secho("Ingestion complete:", fg=typer.colors.GREEN)
    for yr, count in sorted(stats.records_per_year.items()):
        typer.echo(f"  Year {yr}: {count:,} rows")
    typer.echo(f"Total rows: {stats.total_records():,}")


@app.command()
def aggregate(
    raw_dir: Path = typer.Option(Path("data/raw"), help="Directory containing ingested parquet files."),
    processed_dir: Path = typer.Option(
        Path("data/processed"), help="Output directory for aggregated parquet tables."
    ),
    cities_metadata: Path = typer.Option(
        Path("dataset/saveecobot_cities.csv"), help="Path to city metadata CSV."
    ),
    admin_boundaries: Optional[Path] = typer.Option(
        Path("dataset/geo/ukraine_adm_boundaries.geojson"),
        help="Optional path to administrative boundary GeoJSON for spatial joins.",
    ),
    timezone: str = typer.Option("Europe/Kyiv", help="Timezone for local calendar aggregations."),
    wartime_start: str = typer.Option("2022-02-24", help="Start of wartime period (inclusive, ISO date)."),
    pm25_guideline: float = typer.Option(15.0, help="PM2.5 guideline threshold in µg/m³."),
) -> None:
    """Perform hourly-to-daily aggregations and derive summary tables."""
    wartime_start_date = datetime.fromisoformat(wartime_start).date()

    result = aggregate_data(
        raw_dir=_resolve(raw_dir),
        processed_dir=_resolve(processed_dir),
        cities_metadata=_resolve(cities_metadata),
        admin_boundaries=_resolve(admin_boundaries) if admin_boundaries else None,
        timezone=timezone,
        wartime_start=wartime_start_date,
        pm25_guideline=pm25_guideline,
    )
    typer.secho("Aggregation complete:", fg=typer.colors.GREEN)
    for key, value in result.items():
        typer.echo(f"  {key}: {value}")


@app.command()
def qa(
    processed_dir: Path = typer.Option(Path("data/processed"), help="Directory with processed tables."),
    qa_dir: Path = typer.Option(Path("outputs/qa"), help="Directory to write QA plots and reports."),
    pm25_guideline: float = typer.Option(15.0, help="PM2.5 guideline threshold for QA summaries."),
) -> None:
    """Generate QA statistics and plots."""
    qa_summary = run_qa(_resolve(processed_dir), _resolve(qa_dir), pm25_guideline)
    typer.secho("QA complete:", fg=typer.colors.GREEN)
    for key, value in qa_summary.items():
        typer.echo(f"  {key}: {value}")


if __name__ == "__main__":
    app()
