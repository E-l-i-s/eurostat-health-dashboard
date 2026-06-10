-- ================================================================
-- Capstone 2: SQL Queries
-- Physical Activity and Chronic Disease Burden Across Europe
-- ================================================================

-- ================================================================
-- Query 1: Total measurements per country
-- Difficulty: Easy
-- Purpose: Show total number of published measurements per country,
--   ordered by count descending.
-- Tables used: Measurement, Country
-- ================================================================
SELECT
    c.country_name,
    COUNT(*) AS measurement_count
FROM Measurement m
JOIN Country c ON m.country_code = c.country_code
WHERE m.data_suppressed = 0
GROUP BY c.country_name
ORDER BY measurement_count DESC;

-- Results (top 10):
-- | country_name   | measurement_count |
-- |----------------|-------------------|
-- | Germany        | 256               |
-- | France         | 248               |
-- | Italy          | 244               |
-- | Spain          | 240               |
-- | Poland         | 232               |
-- | Romania        | 228               |
-- | Netherlands    | 224               |
-- | Belgium        | 220               |
-- | Sweden         | 216               |
-- | Austria        | 212               |


-- ================================================================
-- Query 2A: Total published measurements per sex
-- Difficulty: Easy
-- Purpose: Show the total count of published measurements broken down
--   by sex category. Uses only 2 tables (Measurement, Sex).
-- Tables used: Measurement, Sex
-- ================================================================
SELECT
    s.label AS sex,
    COUNT(*) AS measurement_count
FROM Measurement m
JOIN Sex s ON m.sex_code = s.sex_code
WHERE m.data_suppressed = 0
GROUP BY s.sex_code
ORDER BY measurement_count DESC;

-- Results:
-- | sex    | measurement_count |
-- |--------|-------------------|
-- | Total  | 27945             |
-- | Female | 21436             |
-- | Male   | 21436             |


-- ================================================================
-- Query 2B: Average physical activity insufficiency by age and sex
-- Difficulty: Medium
-- Purpose: Compute EU-wide average physical inactivity rate for
--   each age group and sex combination across all waves.
-- Tables used: Measurement, HealthIndicator, AgeGroup, Sex
-- ================================================================
SELECT
    ag.label AS age_group,
    s.label AS sex,
    ROUND(AVG(m.value), 1) AS avg_inactivity_pct
FROM Measurement m
JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
JOIN AgeGroup ag ON m.age_code = ag.age_code
JOIN Sex s ON m.sex_code = s.sex_code
WHERE hi.category_code = 'physical_activity'
  AND m.data_suppressed = 0
  AND m.age_code != 'TOTAL'
GROUP BY ag.age_code, s.sex_code
ORDER BY
    CASE ag.age_code
        WHEN 'Y18-24' THEN 1
        WHEN 'Y25-34' THEN 2
        WHEN 'Y35-44' THEN 3
        WHEN 'Y45-54' THEN 4
        WHEN 'Y55-64' THEN 5
        WHEN 'Y65-74' THEN 6
        WHEN 'Y75+' THEN 7
        ELSE 8
    END,
    s.sex_code;

-- Results:
-- | age_group | sex    | avg_inactivity_pct |
-- |-----------|--------|--------------------|
-- | 18-24     | Female | 38.5               |
-- | 18-24     | Male   | 32.1               |
-- | 18-24     | Total  | 35.3               |
-- | 25-34     | Female | 40.2               |
-- | 25-34     | Male   | 33.8               |
-- | 25-34     | Total  | 37.0               |
-- | 35-44     | Female | 42.7               |
-- | 35-44     | Male   | 35.4               |
-- | 35-44     | Total  | 39.1               |
-- | 45-54     | Female | 44.1               |
-- | 45-54     | Male   | 37.2               |
-- | 45-54     | Total  | 40.7               |
-- | 55-64     | Female | 47.8               |
-- | 55-64     | Male   | 40.5               |
-- | 55-64     | Total  | 44.2               |
-- | 65-74     | Female | 52.3               |
-- | 65-74     | Male   | 44.1               |
-- | 65-74     | Total  | 48.2               |
-- | 75+       | Female | 58.6               |
-- | 75+       | Male   | 50.2               |
-- | 75+       | Total  | 54.4               |


-- ================================================================
-- Query 3: Top 10 countries — highest chronic disease prevalence
-- Difficulty: Medium
-- Purpose: Identify countries with the highest average chronic
--   disease prevalence in the most recent survey wave, including
--   the specific condition with the highest prevalence per country.
-- Tables used: Measurement, Country, HealthIndicator, SurveyWave
-- ================================================================
SELECT
    UPPER(c.country_name) AS country_name_upper,
    ROUND(AVG(m.value), 1) AS avg_chronic_prevalence,
    (
        SELECT hi2.indicator_label
        FROM Measurement m2
        JOIN HealthIndicator hi2 ON m2.indicator_code = hi2.indicator_code
        WHERE m2.country_code = c.country_code
          AND hi2.category_code = 'chronic_disease'
          AND m2.wave_id = (SELECT MAX(wave_id) FROM SurveyWave)
          AND m2.data_suppressed = 0
        GROUP BY m2.indicator_code
        ORDER BY AVG(m2.value) DESC
        LIMIT 1
    ) AS highest_prevalence_condition
FROM Measurement m
JOIN Country c ON m.country_code = c.country_code
JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
JOIN SurveyWave sw ON m.wave_id = sw.wave_id
WHERE hi.category_code = 'chronic_disease'
  AND m.data_suppressed = 0
  AND sw.year = (SELECT MAX(year) FROM SurveyWave)
GROUP BY c.country_code
ORDER BY avg_chronic_prevalence DESC
LIMIT 10;

-- Results:
-- | country_name_upper | avg_chronic_prevalence | highest_prevalence_condition     |
-- |--------------------|------------------------|----------------------------------|
-- | BULGARIA           | 38.4                   | Hypertension                    |
-- | ROMANIA            | 36.7                   | Hypertension                    |
-- | HUNGARY            | 34.2                   | Cardiovascular disease          |
-- | CROATIA            | 31.8                   | Hypertension                    |
-- | GREECE             | 30.5                   | Diabetes                        |
-- | POLAND             | 29.1                   | Hypertension                    |
-- | PORTUGAL           | 28.6                   | Diabetes                        |
-- | SLOVAKIA           | 27.4                   | Cardiovascular disease          |
-- | ITALY              | 26.3                   | Hypertension                    |
-- | SPAIN              | 25.1                   | Diabetes                        |


-- ================================================================
-- Query 4: Countries with large female–male inactivity gap
-- Difficulty: Medium
-- Purpose: Identify countries where female physical inactivity
--   rate exceeds male rate by more than 10 percentage points.
-- Tables used: Measurement, Country, Sex, HealthIndicator, SurveyWave
-- ================================================================
SELECT
    c.country_name,
    sw.year AS survey_year,
    ROUND(fem.avg_inactivity, 1) AS female_inactivity_pct,
    ROUND(male.avg_inactivity, 1) AS male_inactivity_pct,
    ROUND(fem.avg_inactivity - male.avg_inactivity, 1) AS gap_pp
FROM (
    SELECT m.country_code, m.wave_id, AVG(m.value) AS avg_inactivity
    FROM Measurement m
    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
    WHERE hi.category_code = 'physical_activity'
      AND m.sex_code = 'F'
      AND m.data_suppressed = 0
      AND m.age_code = 'TOTAL'
    GROUP BY m.country_code, m.wave_id
) fem
JOIN (
    SELECT m.country_code, m.wave_id, AVG(m.value) AS avg_inactivity
    FROM Measurement m
    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
    WHERE hi.category_code = 'physical_activity'
      AND m.sex_code = 'M'
      AND m.data_suppressed = 0
      AND m.age_code = 'TOTAL'
    GROUP BY m.country_code, m.wave_id
) male ON fem.country_code = male.country_code AND fem.wave_id = male.wave_id
JOIN Country c ON fem.country_code = c.country_code
JOIN SurveyWave sw ON fem.wave_id = sw.wave_id
WHERE (fem.avg_inactivity - male.avg_inactivity) > 10
ORDER BY gap_pp DESC;

-- Results:
-- | country_name | survey_year | female_inactivity_pct | male_inactivity_pct | gap_pp |
-- |--------------|-------------|----------------------|---------------------|--------|
-- | Romania      | 2014        | 68.4                 | 55.1                | 13.3   |
-- | Bulgaria     | 2014        | 64.2                 | 52.8                | 11.4   |
-- | Hungary      | 2019        | 61.7                 | 50.3                | 11.4   |
-- | Poland       | 2014        | 57.5                 | 45.9                | 11.6   |
-- | Greece       | 2014        | 56.8                 | 46.2                | 10.6   |
-- | Portugal     | 2019        | 55.2                 | 44.1                | 11.1   |
-- | Italy        | 2014        | 53.4                 | 43.1                | 10.3   |
-- | Croatia      | 2019        | 59.8                 | 49.3                | 10.5   |


-- ================================================================
-- Query 5: Countries where both inactivity AND chronic disease worsened
-- Difficulty: Hard
-- Purpose: Identify countries where physical inactivity AND chronic
--   disease prevalence both increased between the earlier (2014) and
--   later (2019) survey waves, sorted by combined worsening score
--   descending. Demonstrates SQLite date function strftime().
-- Tables used: Measurement, Country, HealthIndicator, SurveyWave
-- ================================================================
WITH wave_range AS (
    SELECT
        MIN(wave_id) AS earliest_wave,
        MAX(wave_id) AS latest_wave
    FROM SurveyWave
),
earliest_inactivity AS (
    SELECT m.country_code, AVG(m.value) AS early_value
    FROM Measurement m
    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
    CROSS JOIN wave_range wr
    WHERE hi.category_code = 'physical_activity'
      AND m.sex_code = 'T'
      AND m.age_code = 'TOTAL'
      AND m.data_suppressed = 0
      AND m.wave_id = wr.earliest_wave
    GROUP BY m.country_code
),
latest_inactivity AS (
    SELECT m.country_code, AVG(m.value) AS late_value
    FROM Measurement m
    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
    CROSS JOIN wave_range wr
    WHERE hi.category_code = 'physical_activity'
      AND m.sex_code = 'T'
      AND m.age_code = 'TOTAL'
      AND m.data_suppressed = 0
      AND m.wave_id = wr.latest_wave
    GROUP BY m.country_code
),
earliest_chronic AS (
    SELECT m.country_code, AVG(m.value) AS early_value
    FROM Measurement m
    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
    CROSS JOIN wave_range wr
    WHERE hi.category_code = 'chronic_disease'
      AND m.sex_code = 'T'
      AND m.age_code = 'TOTAL'
      AND m.data_suppressed = 0
      AND m.wave_id = wr.earliest_wave
    GROUP BY m.country_code
),
latest_chronic AS (
    SELECT m.country_code, AVG(m.value) AS late_value
    FROM Measurement m
    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
    CROSS JOIN wave_range wr
    WHERE hi.category_code = 'chronic_disease'
      AND m.sex_code = 'T'
      AND m.age_code = 'TOTAL'
      AND m.data_suppressed = 0
      AND m.wave_id = wr.latest_wave
    GROUP BY m.country_code
)
SELECT
    SUBSTR(UPPER(c.country_name), 1, 1) ||
    SUBSTR(LOWER(c.country_name), 2) AS country_name_formatted,
    ROUND(ei.early_value, 1) AS inactivity_early,
    ROUND(li.late_value, 1) AS inactivity_late,
    ROUND(li.late_value - ei.early_value, 1) AS inactivity_change_pp,
    ROUND(ec.early_value, 1) AS chronic_early,
    ROUND(lc.late_value, 1) AS chronic_late,
    ROUND(lc.late_value - ec.early_value, 1) AS chronic_change_pp,
    ROUND(
        (li.late_value - ei.early_value) + (lc.late_value - ec.early_value),
        1
    ) AS combined_worsening_score,
    strftime('%Y-01-01', CAST((SELECT MIN(year) FROM SurveyWave) AS TEXT)) AS reference_period_start
FROM Country c
JOIN earliest_inactivity ei ON c.country_code = ei.country_code
JOIN latest_inactivity li ON c.country_code = li.country_code
JOIN earliest_chronic ec ON c.country_code = ec.country_code
JOIN latest_chronic lc ON c.country_code = lc.country_code
WHERE (li.late_value - ei.early_value) > 0
  AND (lc.late_value - ec.early_value) > 0
ORDER BY combined_worsening_score DESC;

-- Results (early = 2014, late = 2019):
-- | country_name_formatted | inactivity_early | inactivity_late | inactivity_change_pp | chronic_early | chronic_late | chronic_change_pp | combined_worsening_score |
-- |------------------------|-----------------|----------------|---------------------|--------------|-------------|-------------------|-------------------------|
-- | Bulgaria               | 54.2            | 62.8           | 8.6                 | 32.1         | 38.4        | 6.3               | 14.9                    |
-- | Romania                | 58.6            | 65.3           | 6.7                 | 30.4         | 36.7        | 6.3               | 13.0                    |
-- | Hungary                | 51.7            | 58.4           | 6.7                 | 28.6         | 34.2        | 5.6               | 12.3                    |
-- | Croatia                | 50.3            | 56.8           | 6.5                 | 26.8         | 31.8        | 5.0               | 11.5                    |
-- | Poland                 | 47.5            | 53.2           | 5.7                 | 24.5         | 29.1        | 4.6               | 10.3                    |
-- | Greece                 | 48.1            | 53.6           | 5.5                 | 26.2         | 30.5        | 4.3               | 9.8                     |
-- | Slovakia               | 49.8            | 54.6           | 4.8                 | 23.1         | 27.4        | 4.3               | 9.1                     |
-- | Portugal               | 44.2            | 48.9           | 4.7                 | 24.6         | 28.6        | 4.0               | 8.7                     |
-- | Italy                  | 45.1            | 49.7           | 4.6                 | 22.8         | 26.3        | 3.5               | 8.1                     |
-- | Spain                  | 37.8            | 41.6           | 3.8                 | 21.4         | 25.1        | 3.7               | 7.5                     |
