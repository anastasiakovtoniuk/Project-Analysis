# Project: Air Quality Dynamics of Ukrainian Cities During War

## Problem Statement
Russia’s full-scale invasion altered activity patterns, infrastructure reliability, and energy usage in Ukraine. These disruptions likely affected ambient particulate matter (PM2.5) concentrations. Hourly PM2.5 measurements collected by SaveEcoBot (crowdsourced and institutional monitors) allow us to compare air-quality dynamics before (2019–2021) and during wartime (2022–present).

## Core Research Questions
- How did PM2.5 level distributions change nationally and by city once the invasion began?
- Which cities experienced the largest shifts in central tendency and in tail behaviour (extreme pollution events)?
- How do seasonal and diurnal PM2.5 patterns differ between the pre-war baseline and wartime period?
- To what degree do data gaps (e.g., outages, damage) influence observed trends?

## Data & Coverage
- Hourly PM2.5 and NowCast AQI CSV exports (2019–2023) per city, sourced from SaveEcoBot via Ukraine’s Diia open-data portal.
- City metadata (`saveecobot_cities.csv`) with administrative identifiers for labelling and joins.
- Optional enrichments: attack intensity timelines, meteorological reanalysis, population estimates.

## Analytical Approach
1. **Ingest** yearly CSVs, harmonize timestamps to `Europe/Kyiv`, and persist to Parquet.
2. **Clean & Validate** by flagging implausible readings, quantifying completeness, and documenting outages.
3. **Aggregate** to daily and yearly features (means, percentiles, exceedance share, AQI category proportions).
4. **Visualize** 5–7 publication-ready graphics that encapsulate distribution shifts, city rankings, inequality, seasonality, exceedances, and sensor coverage context.

## Outputs
- Reproducible Python pipeline (CLI-based) for ingestion, aggregation, and QA diagnostics.
- Publication-ready PNG/SVG figures with consistent aesthetic suitable for reports.
- Documentation: `Datasets-Outline.md`, `Data-Processing-Plan.md`, `Graphics-Outline.md`, plus ongoing QA logs.

## Limitations & Considerations
- Sensor coverage is uneven; weight analyses by data availability and acknowledge biases.
- Outages due to blackouts or damage may obscure true pollution spikes.
- Lack of meteorological controls can confound seasonal comparisons; incorporate when feasible.
