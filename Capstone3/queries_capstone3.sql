-- ===================================================================
-- Capstone 3: Austria Energy Transition - Key SQL Queries
-- PostgreSQL versions used by the Flask API routes
-- ===================================================================

-- Query 1: Energy Mix Evolution
-- Returns yearly generation by source for stacked area / line charts
-- Equivalent to: GET /api/energy_mix
SELECT
    eg.year,
    eg.hydro_twh,
    eg.wind_twh,
    eg.solar_twh,
    eg.biomass_twh,
    eg.coal_twh,
    eg.gas_twh,
    eg.oil_twh
FROM electricity_generation eg
WHERE eg.year BETWEEN 1900 AND 2024
ORDER BY eg.year;

-- Sample output:
--  year | hydro_twh | wind_twh | solar_twh | biomass_twh | coal_twh | gas_twh | oil_twh
-- ------+-----------+----------+-----------+-------------+----------+---------+---------
--  1900 |       5.0 |      0.0 |       0.0 |         2.0 |     20.0 |     0.5 |     2.0
--  1901 |      5.15 |      0.0 |       0.0 |        2.05 |     20.8 |   0.517 |    2.05


-- Query 2: Renewable Share with Policy Milestones
-- Returns renewable percentage and policy flags over time
-- Equivalent to: GET /api/renewable_share
SELECT
    c.year,
    c.renewable_share_pct,
    c.fossil_fuel_share_pct,
    COALESCE(pe.event_name, '') AS policy_event
FROM consumption c
LEFT JOIN policy_event pe ON c.year = pe.year AND pe.flag = 1
ORDER BY c.year;

-- Sample output:
--  year | renewable_share_pct | fossil_fuel_share_pct |       policy_event
-- ------+---------------------+-----------------------+--------------------------
--  1918 |                17.7 |                  82.3 | End of WWI — Energy...
--  1945 |                25.0 |                  75.0 | End of WWII — Infra...


-- Query 3: CO₂ Emissions by Decade
-- Aggregates total CO₂ emissions per decade for bar chart
-- Equivalent to: GET /api/co2_decade
SELECT
    yd.decade,
    ROUND(SUM(e.co2_emissions_mt), 2) AS total_co2
FROM year_dim yd
JOIN emissions e ON yd.year = e.year
GROUP BY yd.decade
ORDER BY yd.decade;

-- Sample output:
--  decade | total_co2
-- --------+-----------
--  1900s  |    81.654
--  1910s  |   159.545


-- Query 4: KPI Summary (Latest Year)
-- Returns current renewable share, CO₂ reduction, intensity change, renewable TWh
-- Equivalent to: GET /api/kpi_summary
WITH latest AS (
    SELECT * FROM consumption ORDER BY year DESC LIMIT 1
),
earliest AS (
    SELECT * FROM consumption ORDER BY year ASC LIMIT 1
),
peak_co2 AS (
    SELECT MAX(co2_emissions_mt) AS peak_value FROM emissions
),
latest_co2 AS (
    SELECT co2_emissions_mt FROM emissions ORDER BY year DESC LIMIT 1
)
SELECT
    latest.renewable_share_pct AS current_renewable_share,
    ROUND(((peak_co2.peak_value - latest_co2.co2_emissions_mt) / peak_co2.peak_value) * 100, 2) AS co2_reduction_pct,
    ROUND(((earliest.energy_intensity - latest.energy_intensity) / earliest.energy_intensity) * 100, 2) AS energy_intensity_change,
    ROUND(latest.total_renewable_twh, 2) AS current_renewable_twh
FROM latest, earliest, peak_co2, latest_co2;

-- Sample output:
--  current_renewable_share | co2_reduction_pct | energy_intensity_change | current_renewable_twh
-- -------------------------+-------------------+-------------------------+-----------------------
--                     42.95 |             35.23 |                   68.75 |                 32.21


-- Query 5: Decade × Source Heatmap
-- Averages generation by source per decade for heatmap visualization
-- Equivalent to: GET /api/heatmap
SELECT
    yd.decade,
    ROUND(AVG(eg.hydro_twh), 2)   AS hydro,
    ROUND(AVG(eg.wind_twh), 2)    AS wind,
    ROUND(AVG(eg.solar_twh), 2)   AS solar,
    ROUND(AVG(eg.biomass_twh), 2) AS biomass,
    ROUND(AVG(eg.coal_twh), 2)    AS coal,
    ROUND(AVG(eg.gas_twh), 2)     AS gas,
    ROUND(AVG(eg.oil_twh), 2)     AS oil
FROM year_dim yd
JOIN electricity_generation eg ON yd.year = eg.year
GROUP BY yd.decade
ORDER BY yd.decade;

-- Sample output:
--  decade | hydro | wind | solar | biomass | coal  | gas  | oil
-- --------+-------+------+-------+---------+-------+------+------
--  1900s  |  5.75 |  0.0 |   0.0 |    2.25 | 23.15 | 0.57 | 2.25
--  1910s  |  8.31 |  0.0 |   0.0 |    3.32 | 28.90 | 2.98 | 3.32
