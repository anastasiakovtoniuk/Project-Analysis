# Data Quality Log

Document known data issues, remediation steps, and outstanding questions here.

| Date | City/Scope | Issue | Action |
| --- | --- | --- | --- |
| 2025-10-18 | National — 2024 | Archive ingest adds ~0.97M hourly rows; after filtering, only city-years with ≥70% coverage remain (92 cities total), leaving limited wartime representation beyond 2023. | Note that 2024–2025 figures reflect the subset meeting coverage thresholds; rerun ingest when fuller data arrives. |
| 2025-10-18 | Donetsk & Zaporizhzhia frontline cities (Добропілля, Зеленодольськ, Бердянськ) — 2022 | share_days_ge18 = 0 despite available readings, indicating prolonged outages or sensor loss. | Flag these cities in reporting; seek alternative sources or annotate charts with coverage caveats. |
| 2025-10-18 | Northern/Western towns (Шепетівка, Стрижавка, Любешів, Грушківці) — 2023 | ≤45% of days with ≥18 hourly records; potential device downtime or data export gaps. | Investigate SaveEcoBot station health; if unresolved, down-weight in wartime comparisons. |
| 2025-10-18 | Васищеве (Kharkivska) & Верховина (Ivano-Frankivska) — 2023 | Mean exceedance share >0.6 with strong coverage; possible local factors driving sustained pollution. | Verify sensor calibration; if confirmed, highlight as hotspots in narrative. |
