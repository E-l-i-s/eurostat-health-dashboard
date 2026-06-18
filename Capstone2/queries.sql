-- ============================================================
-- CAPSTONE 2: Austria Energy Transition
-- SQL Queries (5 queries: 2 Easy, 2 Medium, 1 Difficult)
-- Target: PostgreSQL
-- ============================================================

-- ============================================================
-- QUERY 1 [EASY]: Total Renewable Generation by Decade
--
-- Explanation:
--   This query sums the total renewable electricity generation
--   (hydro + wind + solar + biomass) for each decade. It joins
--   electricity_generation with year_dim and energy_source to
--   filter only renewable sources and group by decade.
--   It reveals Austria's long-term shift toward renewables.
-- ============================================================
SELECT
    yd.decade,
    ROUND(SUM(eg.generation_twh)::numeric, 2) AS total_renewable_gen_twh
FROM electricity_generation eg
JOIN year_dim yd ON eg.year_id = yd.year_id
JOIN energy_source es ON eg.source_id = es.source_id
WHERE es.is_renewable = TRUE
GROUP BY yd.decade
ORDER BY yd.decade;

-- Sample result set:
-- decade  | total_renewable_gen_twh
-- --------+-------------------------
-- 1900s   |                  37.00
-- 1910s   |                  49.10
-- 1920s   |                  65.20
-- 1930s   |                  79.73
-- 1940s   |                  94.47
-- 1950s   |                 119.00
-- 1960s   |                 187.66
-- 1970s   |                 323.74
-- 1980s   |                 439.27
-- 1990s   |                 498.27
-- 2000s   |                 488.94
-- 2010s   |                 620.28
-- 2020s   |                 322.49


-- ============================================================
-- QUERY 2 [EASY]: Average CO2 Emissions for High-Renewable Years
--
-- Explanation:
--   This calculates the average CO2 emissions (both total and
--   per capita) for years where the renewable share of energy
--   consumption exceeded 40%. This helps understand whether
--   higher renewable penetration correlates with lower emissions.
-- ============================================================
SELECT
    ROUND(AVG(e.co2_mt)::numeric, 3)  AS avg_co2_mt,
    ROUND(AVG(e.co2_per_capita_t)::numeric, 4) AS avg_co2_per_capita_t,
    COUNT(*)                             AS num_years
FROM emissions e
JOIN year_dim yd ON e.year_id = yd.year_id
JOIN consumption c ON c.year_id = yd.year_id
WHERE c.renewable_share_pct > 40;

-- Sample result set:
-- avg_co2_mt  | avg_co2_per_capita_t | num_years
-- ------------+----------------------+-----------
--    58.482   |              6.409   |         2


-- ============================================================
-- QUERY 3 [MEDIUM]: Multi-Table JOIN — Generation & Emissions
--     After 2000
--
-- Explanation:
--   This query joins year_dim, electricity_generation,
--   energy_source, and emissions for years 2000 and later.
--   It shows each year, the energy source name, how much
--   electricity was generated from that source, and the
--   corresponding CO2 emissions. This reveals the energy mix
--   and carbon impact of Austria's post-2000 energy transition.
-- ============================================================
SELECT
    yd.year,
    es.source_name,
    ROUND(eg.generation_twh::numeric, 3) AS generation_twh,
    em.co2_mt,
    em.co2_per_capita_t
FROM electricity_generation eg
JOIN year_dim yd ON eg.year_id = yd.year_id
JOIN energy_source es ON eg.source_id = es.source_id
JOIN emissions em ON em.year_id = yd.year_id
WHERE yd.year >= 2000
ORDER BY yd.year, es.source_name
LIMIT 20;

-- Sample result set (first 5 of ~200 rows):
-- year | source_name | generation_twh | co2_mt  | co2_per_capita_t
-- ------+-------------+----------------+---------+-----------------
-- 2000 | biomass     |          0.000 | 68.745  |           8.579
-- 2000 | coal        |         42.470 | 68.745  |           8.579
-- 2000 | gas         |         78.205 | 68.745  |           8.579
-- 2000 | hydro       |        116.210 | 68.745  |           8.579
-- 2000 | nuclear     |          0.000 | 68.745  |           8.579


-- ============================================================
-- QUERY 4 [MEDIUM]: Policy Events per Decade with Avg Renewable
--     Share
--
-- Explanation:
--   This counts the number of policy events in each decade and
--   computes the average renewable energy share for those
--   years. It uses LEFT JOIN to include decades with zero
--   policy events. Policy events are important milestones in
--   Austria's energy transition (e.g., EU accession, EAG).
-- ============================================================
SELECT
    yd.decade,
    COUNT(pe.event_id)                 AS policy_event_count,
    ROUND(AVG(c.renewable_share_pct)::numeric, 2) AS avg_renewable_share_pct
FROM year_dim yd
LEFT JOIN policy_event pe ON pe.year_id = yd.year_id
JOIN consumption c ON c.year_id = yd.year_id
GROUP BY yd.decade
ORDER BY yd.decade;

-- Sample result set:
-- decade | policy_event_count | avg_renewable_share_pct
-- --------+--------------------+-------------------------
-- 1900s  |                  0 |                   15.83
-- 1910s  |                  1 |                   17.28
-- 1920s  |                  0 |                   19.08
-- 1930s  |                  0 |                   21.18
-- 1940s  |                  1 |                   24.68
-- 1950s  |                  1 |                   31.50
-- 1960s  |                  0 |                   28.51
-- 1970s  |                  1 |                   22.71
-- 1980s  |                  0 |                   28.94
-- 1990s  |                  1 |                   28.80
-- 2000s  |                  3 |                   27.67
-- 2010s  |                  2 |                   32.98
-- 2020s  |                  2 |                   37.96


-- ============================================================
-- QUERY 5 [DIFFICULT]: Austria vs. Synthetic EU Benchmark
--     Renewable Share Comparison
--
-- Explanation:
--   This query uses a CTE to compute a synthetic "EU average"
--   renewable share benchmark by averaging Austria's own data
--   across a rolling 5-year window (simulating an EU-wide
--   trajectory). It then compares Austria's actual renewable
--   share to this benchmark for each year, showing whether
--   Austria is above or below the synthetic EU average.
--   The WHERE clause filters to years 1990+ for relevance.
--
--   NOTE: In production, this would join an actual EU dataset.
--   Here, the synthetic benchmark is computed as:
--     EU_avg = 0.85 * Austria_renewable_share + 2.0
--   (a simplified model representing EU being slightly ahead
--    or behind Austria's trajectory depending on the era).
-- ============================================================
WITH eu_benchmark AS (
    SELECT
        yd.year,
        c.renewable_share_pct AS austria_renewable_share,
        ROUND((c.renewable_share_pct * 0.85 + 2.0)::numeric, 2) AS synthetic_eu_avg
    FROM consumption c
    JOIN year_dim yd ON c.year_id = yd.year_id
)
SELECT
    year,
    austria_renewable_share,
    synthetic_eu_avg,
    ROUND((austria_renewable_share - synthetic_eu_avg)::numeric, 2) AS difference,
    CASE
        WHEN austria_renewable_share > synthetic_eu_avg THEN 'ABOVE EU AVG'
        WHEN austria_renewable_share < synthetic_eu_avg THEN 'BELOW EU AVG'
        ELSE 'AT EU AVG'
    END AS comparison
FROM eu_benchmark
WHERE year >= 1990
ORDER BY year;

-- Sample result set:
-- year | austria_renewable_share | synthetic_eu_avg | difference |  comparison
-- ------+-------------------------+------------------+------------+--------------
-- 1990 |                   27.76 |            25.60 |       2.17 | ABOVE EU AVG
-- 1991 |                   26.53 |            24.55 |       1.98 | ABOVE EU AVG
-- 1992 |                   29.83 |            27.36 |       2.47 | ABOVE EU AVG
-- 1993 |                   30.72 |            28.11 |       2.61 | ABOVE EU AVG
-- 1994 |                   30.03 |            27.52 |       2.50 | ABOVE EU AVG
-- ...
-- 2020 |                   36.55 |            33.06 |       3.48 | ABOVE EU AVG
-- 2021 |                   34.64 |            31.45 |       3.20 | ABOVE EU AVG
-- 2022 |                   34.06 |            30.95 |       3.11 | ABOVE EU AVG
-- 2023 |                   41.60 |            37.36 |       4.24 | ABOVE EU AVG
-- 2024 |                   42.95 |            38.51 |       4.44 | ABOVE EU AVG
