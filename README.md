# How War Affects Ukraine’s Ecology

Reproducible analysis of hourly PM2.5 and AQI in Ukrainian cities, comparing pre‑war and wartime periods.

## Quick Start
1) Unpack data
```bash
unzip dataset.zip   # creates dataset/
```
2) Set up environment
```bash
task setup          # creates .venv/ and installs deps
```
3) Run pipeline (ingest → aggregate → QA)
```bash
task pipeline
```
4) Render figures (optional)
```bash
task figures
```

CLI help
```bash
python -m src.pipeline.run --help
python -m src.visualization.run --help
```

## Key Commands
- `task pipeline` — full data prep (writes to `data/processed/`).
- `task full` — pipeline + figures.
- `task clean` — remove outputs under `data/` and `outputs/`.

## Project Layout
- `dataset/` raw CSV exports and `geo/` shapes (git‑ignored; `dataset.zip` kept).
- `data/` pipeline artefacts: `raw/`, `processed/` (git‑ignored).
- `outputs/` figures (`figures/`) and QA (`qa/`) (git‑ignored).
- `src/` Python package: `pipeline/` (Typer CLI), `visualization/`, `lib/`.
- `Taskfile.yml` task runner; `docs/` notes; `notebooks/` ad‑hoc.

## Notes
- WHO PM2.5 24‑hour guideline is 15 µg/m³.
- Eligibility filter: include cities with ≥70% daily coverage in ≥4 years (≥2 pre‑war, ≥2 wartime).
- Choropleth (figure 08) requires `dataset/geo/ukraine_adm_boundaries.geojson`.
- Portions of this project were generated with assistance from an AI model.
