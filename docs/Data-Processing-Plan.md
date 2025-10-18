# Data Processing Plan

## 1. Ingestion (`python -m src.pipeline.run ingest`)
- Stream yearly CSVs in chunks, normalise column names, and coerce numeric types.
- Localise timestamps to UTC, derive Kyiv-local timestamps, and attach source filename for provenance.
- Partition output by year into `data/raw/city_hourly_<year>.parquet` to accelerate downstream reads.
- Supply `--archive-csv dataset/saveecobot-cities-pm25-and-aqi-pm25.csv` to incorporate 2024–2025 records while skipping duplicate 2019–2023 rows contained in the archive export.

## 2. Time Handling
- Convert UTC timestamps to timezone-aware `Europe/Kyiv`; derive `date_local`, `hour_local`, `month`, `year`, `season` labels.
- Maintain original UTC timestamp for reproducibility.

## 3. Quality Checks
- Flag implausible readings (`pm25` outside 0–1000 µg/m³, `aqi` outside 0–500) and retain flags for transparency.
- Propagate available-hour counts to daily summaries; compute exceedance hours (PM2.5 > 15 µg/m³).
- Store QA diagnostics via the dedicated QA stage (`outputs/qa/city_year_coverage.csv`).

## 4. Harmonization & Aggregation (`python -m src.pipeline.run aggregate`)
- Enrich hourly data with calendar keys, seasons, wartime indicator, and city metadata join.
- Aggregate to daily features (mean/median/p90/p10/max PM2.5, available hours, exceedance share, mean AQI).
- Derive city-level summaries for yearly and pre-war/wartime periods, capturing spread and coverage diagnostics.
- Roll up to oblast-level metrics and merge with administrative geometry for choropleth-ready outputs.
- Persist artefacts in `data/processed/` (`city_hourly_pm25.parquet`, `city_daily_pm25.parquet`, `city_distributions.parquet`, `region_period_pm25.parquet`).
- Enforce eligibility: retain only cities with ≥70% daily coverage in at least four years (≥2 pre-war, ≥2 wartime) before writing outputs.

## 5. Feature Engineering
- Maintain derived fields for season, ISO week, wartime status, and calendar attributes within both hourly and daily tables.
- Merge oblast geometry via `region_name`/`koatuu` mapping to support the choropleth heat map.
- Reserve hooks for supplemental joins (attacks, meteorology) on `city_id` and `date_local` once sources are confirmed.

## 6. Validation & Documentation (`python -m src.pipeline.run qa`)
- Summarise coverage and exceedance trends per city-year; export CSV/JSON artefacts to `outputs/qa/`.
- Use QA outputs to identify cities requiring caveats (low coverage, high exceedance variance) and record findings in `docs/data_quality_log.md`.

## 7. Reproducibility
- Implement the pipeline as modular scripts under `src/pipeline/` (e.g., `ingest.py`, `aggregate.py`, `qa.py`).
- Provide CLI entry point (e.g., `python -m src.pipeline.run --stage ingest`) with configuration settings in `config/settings.yaml`.
- All scripts accept `--input-dir`, `--output-dir` to accommodate different storage layouts.

## 8. Figure Rendering
- Use `python -m src.visualization.run all` once processed datasets are available to export the full figure suite to `outputs/figures/`.
- Individual commands (e.g., `python -m src.visualization.run choropleth`) support selective regeneration during iteration.
- Source data for visuals is read from `data/processed/`; ensure pipeline artefacts are refreshed before rendering.
