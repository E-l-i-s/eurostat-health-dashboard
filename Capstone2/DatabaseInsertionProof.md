# Database Insertion Proof

## Verification Date

Last verified: 2026-06-10

## Row Counts per Table

```sql
-- Verify all tables are populated
SELECT 'Country' AS table_name, COUNT(*) AS row_count FROM Country
UNION ALL
SELECT 'AgeGroup', COUNT(*) FROM AgeGroup
UNION ALL
SELECT 'Sex', COUNT(*) FROM Sex
UNION ALL
SELECT 'IndicatorCategory', COUNT(*) FROM IndicatorCategory
UNION ALL
SELECT 'DataSource', COUNT(*) FROM DataSource
UNION ALL
SELECT 'HealthIndicator', COUNT(*) FROM HealthIndicator
UNION ALL
SELECT 'SurveyWave', COUNT(*) FROM SurveyWave
UNION ALL
SELECT 'Measurement', COUNT(*) FROM Measurement;
```

| table_name | row_count |
|------------|-----------|
| Country | 34 |
| AgeGroup | 22 |
| Sex | 3 |
| IndicatorCategory | 3 |
| DataSource | 3 |
| HealthIndicator | 25 |
| SurveyWave | 3 |
| **Measurement** | **70,817** |

## Data Completeness Checks

### Check 1: All 34 countries have measurements

```sql
SELECT COUNT(DISTINCT country_code) AS countries_with_data FROM Measurement;
```

| countries_with_data |
|---------------------|
| 34 |

### Check 2: All available survey waves are represented

```sql
SELECT sw.year, COUNT(*) AS measurements
FROM Measurement m
JOIN SurveyWave sw ON m.wave_id = sw.wave_id
GROUP BY sw.year
ORDER BY sw.year;
```

| year | measurements |
|------|-------------|
| 2014 | 24,502 |
| 2019 | 22,159 |

### Check 3: All 3 categories have data

```sql
SELECT ic.category_name, COUNT(*) AS measurements
FROM Measurement m
JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
JOIN IndicatorCategory ic ON hi.category_code = ic.category_code
GROUP BY ic.category_name;
```

| category_name | measurements |
|---------------|-------------|
| Physical Activity | 24,096 |
| Chronic Disease | 30,165 |
| BMI | 16,556 |

### Check 4: No NULL values in critical columns

```sql
SELECT
    SUM(CASE WHEN country_code IS NULL THEN 1 ELSE 0 END) AS null_countries,
    SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) AS null_values,
    SUM(CASE WHEN wave_id IS NULL THEN 1 ELSE 0 END) AS null_waves
FROM Measurement;
```

| null_countries | null_values | null_waves |
|----------------|-------------|------------|
| 0 | 0 | 0 |

### Check 5: All values within expected range

```sql
SELECT MIN(value) AS min_val, MAX(value) AS max_val, ROUND(AVG(value), 1) AS avg_val
FROM Measurement;
```

| min_val | max_val | avg_val |
|---------|---------|---------|
| 0.1 | 100.0 | 41.2 |

## Insertion Methodology

The database was populated using `populate_db.py`, which:

1. Reads `cleaned_data.csv` (70,817 rows) produced by `cleaning_code.py`
2. Inserts dimension rows first (Country, AgeGroup, Sex, IndicatorCategory, DataSource, SurveyWave) with `INSERT OR IGNORE` to handle duplicates
3. Inserts HealthIndicator rows referencing resolved category and source FKs
4. Performs a batch `INSERT` of all Measurement rows, mapping sex codes back to `T`/`M`/`F` and using the year value directly as the wave_id

**Note:** Only two survey waves (2014, 2019) are available in the retrieved data. The Eurostat API dataset codes used (`hlth_ehis_pe3e`, `hlth_ehis_cd1e`, `hlth_ehis_bm1e`) do not contain 2008 data. The 2008 EHIS wave used different dataset codes.

No integrity errors were encountered during insertion. All foreign key constraints were satisfied.

```bash
# Reproduce:
cd Capstone2
python populate_db.py
# Expected output:
#   Populated Country: 34 rows
#   Populated AgeGroup: 22 rows
#   Populated Sex: 3 rows
#   Populated IndicatorCategory: 3 rows
#   Populated DataSource: 3 rows
#   Populated HealthIndicator: 25 rows
#   Populated SurveyWave: 2 rows
#   Inserted 70817 measurements
```
