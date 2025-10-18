"""Ingestion utilities for SaveEcoBot hourly PM2.5 data."""
from __future__ import annotations

import glob
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from zoneinfo import ZoneInfo


@dataclass
class IngestStats:
    """Summary of records written during ingestion."""

    records_per_year: Counter

    def total_records(self) -> int:
        return sum(self.records_per_year.values())


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    expected_cols = {"city_id", "aqi", "pm25", "logged_at"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    df["city_id"] = pd.to_numeric(df["city_id"], errors="coerce").astype("Int64")
    df["aqi"] = pd.to_numeric(df["aqi"], errors="coerce").astype("float64")
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce").astype("float64")
    df["logged_at"] = pd.to_datetime(df["logged_at"], utc=True, errors="coerce")
    return df


def _iter_hourly_frames(path: Path, chunksize: int = 250_000) -> Iterable[pd.DataFrame]:
    reader = pd.read_csv(
        path,
        chunksize=chunksize,
        dtype={"city_id": "Int64"},
    )
    for chunk in reader:
        yield _normalise_columns(chunk)


def ingest_hourly(
    hourly_pattern: str,
    cities_metadata: Path,
    raw_dir: Path,
    timezone: str = "Europe/Kyiv",
    year: Optional[int] = None,
    archive_csv: Optional[Path] = None,
) -> IngestStats:
    """Load hourly CSV files, normalise timestamps, and persist yearly parquet outputs."""

    raw_dir.mkdir(parents=True, exist_ok=True)
    files = [Path(p) for p in sorted(glob.glob(hourly_pattern))]

    existing_years = {
        int(match.group(1))
        for path in files
        if (match := re.search(r"(20\d{2})", path.stem))
    }

    if archive_csv is not None:
        archive_csv = archive_csv.expanduser()
        if not archive_csv.exists():
            raise FileNotFoundError(f"Archive CSV not found: {archive_csv}")
        files.append(archive_csv)

    if not files:
        raise FileNotFoundError(f"No files matched pattern: {hourly_pattern}")

    # Ensure metadata exists (even if not yet used) to fail fast when misconfigured.
    if not cities_metadata.exists():
        raise FileNotFoundError(f"Cities metadata not found: {cities_metadata}")

    tzinfo = ZoneInfo(timezone)
    writers: Dict[int, pq.ParquetWriter] = {}
    stats = Counter()

    try:
        for path in files:
            is_archive = archive_csv is not None and path == archive_csv
            for chunk in _iter_hourly_frames(path):
                chunk = chunk.dropna(subset=["logged_at", "city_id"])
                if chunk.empty:
                    continue
                chunk["source_file"] = path.name
                chunk["logged_at_local"] = chunk["logged_at"].dt.tz_convert(tzinfo)
                chunk["year"] = chunk["logged_at_local"].dt.year

                if is_archive:
                    chunk = chunk[~chunk["year"].isin(existing_years)]
                    if chunk.empty:
                        continue

                if year is not None:
                    chunk = chunk[chunk["year"] == year]
                    if chunk.empty:
                        continue

                for yr, frame in chunk.groupby("year"):
                    table = pa.Table.from_pandas(
                        frame[
                            [
                                "city_id",
                                "aqi",
                                "pm25",
                                "logged_at",
                                "logged_at_local",
                                "source_file",
                                "year",
                            ]
                        ],
                        preserve_index=False,
                    )
                    target = raw_dir / f"city_hourly_{yr}.parquet"
                    writer = writers.get(yr)
                    if writer is None:
                        if target.exists():
                            target.unlink()
                        writers[yr] = pq.ParquetWriter(target, table.schema)
                        writer = writers[yr]
                    writer.write_table(table)
                    stats[yr] += table.num_rows
    finally:
        for writer in writers.values():
            writer.close()

    if not stats:
        raise RuntimeError("No records ingested; check filters and source data")

    return IngestStats(records_per_year=stats)


__all__ = ["ingest_hourly", "IngestStats"]
