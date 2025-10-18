# Graphics Outline

1. **National Distribution Shift (Pre-war vs Wartime)**
   - **Goal:** Show how the overall PM2.5 distribution changed between 2019–2021 and 2022–2023.
   - **Data:** `city_hourly_pm25` (hourly or daily means aggregated nationally).
   - **Form:** Side-by-side density ridges or violin plots comparing distributions of daily mean PM2.5.
   - **Notes:** Weight cities by observation count to avoid bias from sparse sensors.

2. **City Median Ladder Chart**
   - **Goal:** Rank cities by median PM2.5 for pre-war and wartime periods to highlight relative shifts.
   - **Data:** `city_daily_pm25` aggregated by city and period.
   - **Form:** Paired dot chart (slopegraph) or dumbbell plot with inline labels.
   - **Notes:** Include only cities with ≥70% data availability per period.

3. **Inequality Panel (p90–p10 Gap)**
   - **Goal:** Measure intra-city variability and extremes.
   - **Data:** Percentile metrics from `city_distributions`.
   - **Form:** Small-multiples line chart tracking yearly p90, median, p10 per selected cities.
   - **Notes:** Highlight war years with background shading.

4. **Seasonal Heatmap (Hour × Month)**
   - **Goal:** Reveal typical diurnal/seasonal patterns and wartime deviations.
   - **Data:** Hourly data resampled to average by `month` and `hour_local`.
   - **Form:** 24×12 heatmap per period (pre-war vs wartime) shown stacked.
   - **Notes:** Convert timestamps to Kyiv local time; annotate daylight-saving transitions.

5. **Exceedance Timeline**
   - **Goal:** Track share of hours exceeding WHO 24h guideline (15 µg/m³) through time.
   - **Data:** `city_daily_pm25` with computed exceedance proportions.
   - **Form:** Rolling 30-day line chart for key cities plus national average.
   - **Notes:** Add markers for major conflict events when data available.

6. **Station Coverage Barline**
   - **Goal:** Contextualize availability and reliability by showing number of active sensors per city over time.
   - **Data:** Requires station-level metadata (if absent, approximate via distinct sensors per city-day or use external dataset).
   - **Form:** Area or barline overlay per city.
   - **Notes:** If station metadata cannot be sourced, replace with completeness percentage plot.

7. **AQI vs PM2.5 Scatter Pulse**
   - **Goal:** Illustrate relationship between PM2.5 concentration and AQI classification.
   - **Data:** Hourly records with both metrics.
   - **Form:** Hexbin or contour plot separately for pre-war and wartime.
   - **Notes:** Use US EPA AQI breakpoints to annotate category bands.

8. **Choropleth Heat Map**
   - **Goal:** Compare spatial patterns of average PM2.5 (or exceedance share) across Ukrainian cities/regions for pre-war vs wartime periods.
   - **Data:** `city_daily_pm25` aggregated to period-level metrics joined with administrative boundaries (`katottg`/`koatuu` polygons).
   - **Form:** Split-panel choropleth (pre-war vs wartime) with unified color scale, minimal basemap styling.
   - **Notes:** Use simplified GeoJSON for performance; ensure cities without geometry fall back to point markers or are listed separately.

Each figure should export a 2400×1350 PNG (and optionally SVG) with consistent minimal styling suitable for publication.
