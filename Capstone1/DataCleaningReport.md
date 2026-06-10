# Data Cleaning Report

## Overview

Raw Eurostat JSON:stat data was retrieved from three API endpoints (`hlth_ehis_pe3e`, `hlth_ehis_cd1e`, `hlth_ehis_bm1e`) and processed through five cleaning steps before insertion into the relational database. This report documents each transformation against the actual `cleaning_code.py` implementation and the resulting `cleaned_data.csv`.

## Cleaning Steps

### Step 1 — Suppression Flagging

- **Action:** Count suppressed rows where Eurostat flagged data as suppressed for confidentiality (small-cell counts with n < 5).
- **Code:** `df["data_suppressed"].sum()` — values are flagged, **never removed**.
- **Decision:** Suppressed values are retained in the dataset with a boolean flag (`data_suppressed = True`). Imputation would introduce bias; exclusion with flagging preserves the ability to run analyses with or without suppressed data.
- **Rows flagged:** 0 (all `data_suppressed` values are `False` in the retrieved data — suppression flags may arrive as metadata rather than row-level fields in JSON:stat format).

### Step 2 — Duplicate Removal on Composite Key

- **Action:** Remove exact duplicate rows where all five composite-key fields match: `(geo, time, sex, age, indicator_code)`.
- **Code:** `df.drop_duplicates(subset=composite_key, keep="first")` at `cleaning_code.py:52`.
- **Decision:** The three source datasets share the same dimension structure, so concatenation can produce overlapping rows for identical country–year–sex–age–indicator combinations. Keeping the first occurrence and discarding duplicates ensures each measurement appears exactly once.
- **Rows removed:** 630 (71,447 → 70,817).

### Step 3 — Data Type Normalization

- **Action:** Cast columns to correct types: `time` → integer, `value` → float, `geo` → uppercase string, `age` → ordered categorical.
- **Code:** `pd.to_numeric(...)`, `.astype(str).str.upper()`, `pd.CategoricalDtype(...)` at lines 56–61.
- **Decision:** Consistent types prevent downstream merge and query errors. The ordered age categorical preserves the natural life-course ordering (Y15-19 < Y25-34 < Y65-74, etc.) for sorting.

### Step 4 — Outlier Flagging (3.0 × IQR, Per Indicator)

- **Action:** Flag extreme values within each `indicator_code` group using the interquartile range method at a threshold of 3.0 × IQR.
- **Code:** `q1 - 3.0 * iqr` / `q3 + 3.0 * iqr` at `cleaning_code.py:71-72`.
- **Decision:** 3.0 × IQR is used instead of the conventional 1.5 × IQR because EHIS percentage values are bounded 0–100 and the wider threshold reduces false positives. Outliers are **flagged only, never removed** — all 70,817 rows remain.
- **Rows flagged:** 489 (as `is_outlier_flagged = True` in the CSV).

### Step 5 — Sex Code Standardisation + Column Selection

- **Action:** Map single-letter API codes (`T`, `M`, `F`) to full labels (`Total`, `Male`, `Female`).
- **Code:** `df["sex"].map({"T": "Total", "M": "Male", "F": "Female"})` at line 82.
- **Decision:** Readability for CSV consumers; the mapping is reversed back to codes during database insertion.
- **Final schema:** 15 standardized columns selected at `cleaning_code.py:118-123`.

## Before and After Counts

| Stage | Row Count | Notes |
|---|---|---|
| Raw API data | 71,447 | Combined from 3 Eurostat endpoints |
| After duplicate removal | 70,817 | 630 duplicates removed on composite key |
| After outlier flagging | 70,817 | 489 flagged, 0 removed |
| After sex standardisation | 70,817 | Values unchanged |
| **Final cleaned CSV** | **70,817 rows, 15 columns** | Ready for DB population |

## Column Schema (Cleaned Dataset)

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | geo | TEXT | ISO 3166-1 alpha-2 country code |
| 2 | country_name | TEXT | Full country name in English |
| 3 | time | INTEGER | Survey year (2014 or 2019) |
| 4 | sex | TEXT | Total / Male / Female |
| 5 | age_group | TEXT | EHIS age group code (TOTAL, Y18-24, …) |
| 6 | indicator_code | TEXT | Eurostat indicator short code |
| 7 | indicator_label | TEXT | Human-readable indicator name |
| 8 | indicator_category | TEXT | Physical Activity / Chronic Disease / BMI |
| 9 | value | REAL | Numeric percentage value |
| 10 | unit | TEXT | Unit of measurement (PC) |
| 11 | data_suppressed | BOOL | True if Eurostat suppressed the cell |
| 12 | is_outlier_flagged | BOOL | True if flagged by 3×IQR outlier rule |
| 13 | source_dataset | TEXT | Originating Eurostat dataset code |
| 14 | ehis_wave | TEXT | EHIS wave label |
| 15 | last_retrieved | TEXT | Date of last API retrieval (ISO 8601) |

## Key Cleaning Decisions

1. **3.0×IQR outlier detection** replaces the standard 1.5×IQR because percentage data bounded 0–100 produces many false positives at the narrower threshold.
2. **Outliers are flagged, not removed**, because every data point in an official Eurostat release represents a real survey response. Removing them would discard valid measurements.
3. **No rows were removed for suppression** — the retrieved JSON:stat data had no row-level suppression flags set.
4. **Duplicates were the sole cause of row reduction** (630 rows, all on the composite key `geo + time + sex + age + indicator_code`).
5. **Sex labels are normalised** to `Total`/`Male`/`Female` for CSV readability, then mapped back to `T`/`M`/`F` during database insertion.
6. **Only two survey waves** (2014, 2019) were returned by the Eurostat API for the dataset codes used. The 2008 EHIS wave used different dataset codes and is not included.

## Source Code Reference

```bash
# Reproduce:
python collection_code.py     # → uncleaned_data.csv (~71,447 rows)
python cleaning_code.py       # → cleaned_data.csv (70,817 rows, 15 cols)
```
