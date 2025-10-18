# How War Affects Ukraine’s Ecology

Minimal, reproducible analysis of hourly PM2.5 and AQI dynamics in Ukrainian cities before and during Russia’s full-scale invasion.

## Repository Layout
- `dataset/` — source CSV exports from SaveEcoBot (hourly PM2.5/AQI plus city metadata).
- `data/` — pipeline outputs (`raw/`, `processed/`).
- `src/` — Python package with pipeline stages and figure scripts.
- `notebooks/` — ad-hoc exploration (kept lightweight; pipeline remains primary).
- `outputs/` — publication-ready graphics (`figures/`) and QA artefacts (`qa/`).
- `config/` — configuration templates (e.g., `settings.example.yaml`).
- `docs/` — auxiliary documentation (quality log, notes).
- `Taskfile.yml` — reusable commands powered by [taskfile.dev](https://taskfile.dev).

## Setup
1. Bootstrap the environment via Taskfile:
   ```bash
   task setup
   ```
   (Creates `.venv/`, upgrades `pip`, and installs the pinned requirements.)
2. Unzip `dataset.zip` into the project root so that raw CSVs live under `dataset/` (the folder is git-ignored).
   ```bash
   unzip dataset.zip
   ```
3. Copy `config/settings.example.yaml` to `config/settings.yaml` and adjust paths if your data lives elsewhere.

## Data Pipeline
- Run ingest → aggregate → QA in one go:
  ```bash
  task pipeline
  ```
- To include figure rendering as well:
  ```bash
  task full
  ```

## Figure Generation
- Render the full figure bundle:
  ```bash
  task figures
  ```
- Individual visuals are available via `python -m src.visualization.run --help`. Figures are written to `outputs/figures/`.
- City-level plots automatically filter to sensors with ≥70% daily coverage in at least four years (≥2 pre-war and ≥2 wartime) to keep comparisons consistent.

Choropleth maps require administrative boundary geometries stored under `dataset/geo/` (already included as `ukraine_adm_boundaries.geojson`).

## Next Steps
- Finalize ingestion and aggregation code.
- Acquire supplemental datasets noted in `Datasets-Outline.md` (administrative boundaries, attacks timeline, meteorology as needed).
- Populate notebooks with exploratory diagnostics once the pipeline stabilizes.
