# Dashboard Plan — Austria Energy Transition (Capstone 3)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flask Application                        │
│  ┌──────────────┐  ┌─────────────────────┐  ┌───────────────┐  │
│  │  Template     │  │   REST API          │  │  SQLAlchemy   │  │
│  │  Engine       │──│   (JSON endpoints)  │──│  ORM          │  │
│  │  (Jinja2)     │  │                     │  │  (SQLite)     │  │
│  └──────────────┘  └─────────────────────┘  └───────┬───────┘  │
│                                                      │          │
│                              ┌───────────────────────┘          │
│                              │  CSV → SQLite on startup          │
│                              │  (austria_energy_final.csv)        │
│                              └────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
┌───────────────────┐  ┌──────────────────────┐
│  Dashboard 1      │  │  Dashboard 2         │
│  Strategic View   │  │  Analytical View     │
│  (/)              │  │  (/analytical)       │
│                   │  │                      │
│  Chart.js CDN     │  │  Chart.js + HTML     │
│  Dynamic AJAX     │  │  Heatmap div grid    │
│  No page reloads  │  │  Data table w/       │
│                   │  │  search & pagination │
└───────────────────┘  └──────────────────────┘
```

## Technology Stack

- **Backend:** Python 3 + Flask (lightweight WSGI web framework)
- **ORM:** Flask-SQLAlchemy with SQLAlchemy 2.0 (maps to SQLite)
- **Frontend:** Chart.js (CDN-loaded) for data visualization
- **Data Layer:** Pandas-read CSV → SQLite on application startup
- **Communication:** RESTful JSON API (AJAX fetch from browser)

## API Route Specifications

| Endpoint | Method | Parameters | Returns |
|---|---|---|---|
| `/` | GET | — | Dashboard 1 HTML |
| `/analytical` | GET | — | Dashboard 2 HTML |
| `/api/energy_mix` | GET | `min_year`, `max_year` | `[{year, hydro_twh, wind_twh, solar_twh, biomass_twh, coal_twh, gas_twh, oil_twh}]` |
| `/api/renewable_share` | GET | — | `{years: [...], shares: [...], policies: [{year, event_name}]}` |
| `/api/co2_decade` | GET | — | `{labels: [...], values: [...]}` |
| `/api/kpi_summary` | GET | — | `{current_renewable_share, co2_reduction_pct, energy_intensity_change, current_renewable_twh}` |
| `/api/renewable_growth` | GET | — | `{years: [...], hydro: [...], wind: [...], solar: [...], biomass: [...]}` |
| `/api/intensity_vs_gdp` | GET | — | `{datapoints: [{year, energy_intensity, gdp_per_capita, total_consumption}]}` |
| `/api/heatmap` | GET | — | `{decades: [...], sources: [...], values: [[...]]}` |
| `/api/compare_eu` | GET | — | `{austria: [...], eu_average: [...]}` |

## Dashboard Layouts

### Dashboard 1 — Strategic (Government Policymakers)
```
┌──────────────────────────────────────────────────────────┐
│  HEADER: Austria Energy Transition — Strategic Dashboard  │
├──────────────────────────────────────────────────────────┤
│  FILTERS: Year Range Slider | Source Checkboxes           │
├────────────┬────────────┬────────────┬───────────────────┤
│  KPI:      │  KPI:      │  KPI:      │  KPI:             │
│  Renewable │  CO₂       │  Energy    │  Renewable        │
│  Share     │  Reduction │  Intensity │  Generation (TWh) │
├────────────┴────────────┴────────────┴───────────────────┤
│  CHART 1: Stacked Area — Energy Mix Evolution (full w.)  │
├──────────────────────────────────────────────────────────┤
│  CHART 2: Line — Renewable Share + Policies (full width) │
├──────────────────────────┬───────────────────────────────┤
│  CHART 3: Bar — CO₂      │  CHART 4: Grouped Bar —       │
│  by Decade               │  Austria vs EU Share          │
└──────────────────────────┴───────────────────────────────┘
```

### Dashboard 2 — Analytical (Researchers/Analysts)
```
┌──────────────────────────────────────────────────────────┐
│  HEADER: Austria Energy Transition — Analytical Dashboard │
├──────────────────────────────────────────────────────────┤
│  FILTERS: Source Dropdown | Decade Selector | Metric Sel. │
├──────────────────────────────────────────────────────────┤
│  CHART 1: Multi-line — Renewable Source Growth (full w.) │
├──────────────────────────────────────────────────────────┤
│  CHART 2: Scatter — Intensity vs GDP per Capita (full w.)│
├──────────────────────────┬───────────────────────────────┤
│  CHART 3: Heatmap Grid   │  CHART 4: Grouped Bar — YoY   │
│  (Decade × Source)       │  Change (Last 10 Years)       │
├──────────────────────────┴───────────────────────────────┤
│  CHART 5: Data Table with Search & Pagination (full w.)  │
└──────────────────────────────────────────────────────────┘
```

## User Interaction Flow

1. User loads `/` or `/analytical` → Flask renders HTML template
2. HTML includes `<script src="/static/js/charts.js">` which calls `initDashboard1()` or `initDashboard2()`
3. JavaScript fires parallel `fetch()` calls to all `/api/` endpoints
4. Each response is parsed and passed to a dedicated `render*()` function
5. `render*()` functions create/destroy Chart.js chart instances or update DOM
6. Filter changes (slider, checkboxes, dropdowns) trigger re-fetch and re-render of relevant charts
7. No page reloads occur — all updates are AJAX-driven

## Data Flow Diagram

```
CSV File (austria_energy_final.csv)
    │
    ▼ (app startup — load_csv_data)
SQLite Database (energy.db)
    │
    ▼ (SQLAlchemy ORM queries)
REST API JSON Responses
    │
    ▼ (fetch() — AJAX)
Browser JavaScript (charts.js)
    │
    ├─► Chart.js Canvas Rendering
    ├─► KPI Card DOM Updates
    ├─► Heatmap Grid DOM Generation
    └─► Data Table with Pagination
```

## Color Scheme Rationale

| Color | Hex Code | Usage | Rationale |
|---|---|---|---|
| Green | `#2E7D32` | Renewable energy, Austria line, KPI accent | Associations with clean energy, growth, sustainability |
| Blue | `#1565C0` | Hydro power, CO₂ charts | Water association for hydro; trust/authority for emissions |
| Dark Gray | `#424242` | Fossil fuels (coal), text | Neutral, serious tone for carbon-intensive sources |
| Amber | `#F57F17` | Policy annotations, energy intensity | Warning/attention color for policy milestones |
| Yellow | `#FDD835` | Solar power | Sun association |
| Red | `#EF5350` | Natural gas | Warm/cool contrast in fossil fuel palette |
| Brown | `#795548` | Biomass | Earthy, organic association |
| Purple | `#7B1FA2` | EU average comparison | Distinct from Austria green for contrast |
| Dark BG | `#1a1a2e` | Header background | Professional dark header for formal appearance |
| Light BG | `#f5f7fa` | Page background | Clean, modern light gray background |
