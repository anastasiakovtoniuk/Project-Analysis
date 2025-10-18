# Project: Air Quality Dynamics of Ukrainian Cities During War

## Problem Statement
Russia’s full-scale invasion reshaped mobility patterns, industrial activity, and the reliability of basic infrastructure across Ukraine. These shifts almost certainly influenced ambient particulate matter (PM2.5) concentrations recorded by the SaveEcoBot monitoring network. By combining pre-war (2019–early 2022) and wartime (February 2022 onward) observations, we can benchmark how air quality evolved nationally and in individual cities while highlighting where data gaps complicate interpretation.

## Core Research Questions
- How did PM2.5 distributions (mean, median, tail behaviour) change between the pre-war baseline and wartime period?
- Which cities experienced the largest shifts in central tendency and extremes once hostilities escalated?
- How did diurnal and seasonal PM2.5 cycles respond to wartime disruptions?
- What role do outages and sparse coverage play in shaping the observed trends, and how can we surface those uncertainties?

## Data & Coverage
- Hourly PM2.5 and NowCast AQI exports aggregated by SaveEcoBot (crowdsourced + institutional sensors) covering **2019-02-27 through 2025-01-31**; distributed as yearly CSVs plus a combined archive via data.gov.ua / Diia.
- City metadata (`saveecobot_cities.csv`) supplying Ukrainian/Romanised names, KOATUU/KATOTTG identifiers, and administrative context.
- Administrative boundaries (`ukraine_adm_boundaries.geojson`) used to map oblast-level aggregates.
- Optional enrichments for future iterations: conflict intensity timelines, ERA5 meteorology, population exposure estimates.
- **Eligibility filter:** only cities with ≥70 % daily coverage in at least four calendar years (≥2 pre-war and ≥2 wartime) are retained, leaving 92 consistently monitored locations for cross-period comparisons.

## Analytical Approach
1. **Ingest** per-year CSVs plus the combined archive, normalise column types, localise timestamps to `Europe/Kyiv`, and persist yearly Parquet partitions.
2. **Clean & Validate** by flagging implausible values, computing hourly availability, and deriving coverage metrics for every city-year.
3. **Filter** out city-years failing the eligibility rule before aggregating to daily, yearly, and regional tables, ensuring like-for-like comparisons.
4. **Aggregate** to daily statistics (mean/median/p90/p10/max PM2.5, exceedance share) and build city + oblast summaries for pre-war vs wartime periods.
5. **Visualise** a suite of publication-ready graphics (distribution shift, city ranking, inequality panel, seasonal heatmap, exceedance timeline, station coverage, AQI vs PM2.5, choropleth) exported at consistent resolution.
6. **Document** QA results (coverage tables, narrative caveats) so the analytical story remains transparent.

## Outputs
- Reproducible Python pipeline (Typer CLI + Taskfile) covering ingestion, aggregation, QA, and figure rendering.
- Parquet datasets under `data/processed/` restricted to the eligible sensor network, enabling downstream analysis or notebook exploration.
- Publication-ready PNG figures under `outputs/figures/` with consistent styling and shared scales.
- Living documentation: `Datasets-Outline.md`, `Data-Processing-Plan.md`, `Graphics-Outline.md`, this project brief, and `docs/data_quality_log.md` capturing known caveats.

## Limitations & Considerations
- Frontline areas still suffer sensor attrition; even with eligibility filters, some regions (e.g., occupied territories) remain data-sparse and are marked transparently (grey) on choropleths.
- Meteorological variability is not yet controlled for, so seasonal anomalies may reflect weather rather than policy or conflict effects; future iterations should incorporate ERA5 or local met data.
- AQI/PM2.5 conversions rely on SaveEcoBot’s NowCast implementation; calibration drift or device quality differences persist as latent uncertainties.
- The pipeline assumes future data drops follow current schema; any break in column formats will require ingest adjustments.
