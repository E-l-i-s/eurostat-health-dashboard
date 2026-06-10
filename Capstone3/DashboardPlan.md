# Dashboard Plan

## Dashboard 1 — Strategic (Executive)

**Type:** Strategic

**Audience:** EU and national public health policymakers, ministry advisors, health system administrators who need a high-level overview of which countries require intervention.

**Story:** Which European countries face the greatest combined burden of physical inactivity and chronic disease — and where is the gap between physical activity rates and chronic disease outcomes widest?

**Key Metrics:**
- EU average physical inactivity rate
- EU average chronic disease prevalence
- Count of high-burden countries (inactivity >45% AND chronic prevalence >30%)
- Most improved country since last survey wave

**Required Visualizations:**
1. Choropleth map (Leaflet) — inactivity rate by country, color-coded by quantile
2. Horizontal bar chart — top 10 high-burden countries by combined score
3. KPI summary cards — 4 cards showing headline metrics
4. Trend line — EU average inactivity rate across survey waves
5. Classification table — all countries with risk band badges

**Interactive Elements:** Country filter, condition type dropdown, survey wave selector, sex filter (Total/Male/Female)

## Dashboard 2 — Analytical (Tactical)

**Type:** Analytical

**Audience:** Regional health planners, epidemiologists, academic researchers who need to explore relationships between physical activity and specific chronic conditions at the demographic level.

**Story:** How do physical activity patterns relate to specific chronic conditions across demographic groups — and which age/sex segments show the strongest association?

**Key Metrics:**
- Inactivity rate vs. condition prevalence per country (scatter)
- Year-on-year change within countries
- Condition-specific prevalence breakdowns

**Required Visualizations:**
1. Scatter plot — inactivity rate vs. condition prevalence, one point per country
2. Grouped bar chart — activity by age group for selected country
3. Heatmap — country × condition matrix with CSS intensity coloring
4. Histogram — value distribution for selected indicator
5. Stacked area chart — EU trend broken down by sex

**Interactive Elements:** Country multi-select, condition selector, age group checkboxes, sex toggle, wave comparison slider (Wave A vs Wave B)

## Database Integration Queries

The following 6 SQL queries power the dashboard API endpoints:

1. **query_map_data** — Returns country code + value for choropleth rendering. Filters by indicator, wave year, sex. Used by Dashboard 1 map.

2. **query_kpi_summary** — Returns 4 KPI values: EU average inactivity, EU average chronic prevalence, high-burden country count, most improved country. Used by Dashboard 1 KPI cards.

3. **query_top_countries** — Returns top N countries by indicator value with country name. Used by Dashboard 1 horizontal bar chart.

4. **query_trend** — Returns EU average value per survey wave. Used by Dashboard 1 trend line.

5. **query_scatter** — Returns paired inactivity + prevalence values per country. Used by Dashboard 2 scatter plot.

6. **query_age_breakdown** — Returns values by age group and sex for grouped bar chart. Used by Dashboard 2 by-age analysis.
