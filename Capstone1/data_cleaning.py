"""
data_cleaning.py
Austria Energy Transition Capstone Project — Data Cleaning Module

Reads austria_energy_raw.csv and applies a systematic cleaning pipeline to
produce austria_energy_final.csv.

Cleaning steps:
  1. Load and inspect
  2. Handle missing values (interpolation for time series)
  3. Remove duplicate rows
  4. Normalise numeric formats
  5. Validate internal consistency (share sums, source totals)
  6. Detect outliers (IQR method)
  7. Ensure consistent year formatting
  8. Add derived columns (co2_per_capita, decade, totals)
  9. Write cleaned output

Usage:
    python data_cleaning.py

Output:
    ../Capstone1/austria_energy_final.csv
"""

import csv
import math
import os
import statistics

IN_DIR = os.path.dirname(os.path.abspath(__file__))
raw_path = os.path.join(IN_DIR, 'austria_energy_raw.csv')

# ──────────────────────────────────────────────────────────────────────
# 1.  LOAD
# ──────────────────────────────────────────────────────────────────────
with open(raw_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    raw_rows = list(reader)

print(f"[1] Loaded {len(raw_rows)} rows")
print(f"    Columns: {list(raw_rows[0].keys())}")

# ──────────────────────────────────────────────────────────────────────
# 2.  PARSE & HANDLE MISSING VALUES
# ──────────────────────────────────────────────────────────────────────
# Strategy: linear interpolation for numeric time-series columns.
# For leading gaps, forward-fill from the first known value.
# For trailing gaps, backward-fill from the last known value.
# Binary flags (policy_event_flag) default to 0.

NUMERIC_COLS = [
    'total_energy_consumption_twh', 'renewable_share_pct', 'fossil_fuel_share_pct',
    'co2_emissions_mt', 'hydro_twh', 'wind_twh', 'solar_twh', 'biomass_twh',
    'nuclear_twh', 'coal_twh', 'gas_twh', 'oil_twh', 'energy_intensity',
    'gdp_usd', 'population',
]
INT_COLS = ['year', 'policy_event_flag']
STR_COLS = ['energy_source']

# Parse into structured list
parsed = []
for row in raw_rows:
    p = {}
    for k in NUMERIC_COLS:
        v = row.get(k, '').strip()
        if v == '' or v == 'nan':
            p[k] = None
        else:
            try:
                p[k] = float(v)
            except (ValueError, TypeError):
                p[k] = None
    for k in INT_COLS:
        v = row.get(k, '').strip()
        try:
            p[k] = int(float(v))
        except (ValueError, TypeError):
            p[k] = 0
    for k in STR_COLS:
        p[k] = row.get(k, '').strip()
    parsed.append(p)

# Count and report missing
missing_counts = {}
for k in NUMERIC_COLS:
    n_missing = sum(1 for p in parsed if p[k] is None)
    if n_missing > 0:
        missing_counts[k] = n_missing
        print(f"    Missing '{k}': {n_missing} values")

# Interpolate missing numeric values
for k in NUMERIC_COLS:
    vals = [p[k] for p in parsed]
    # Find indices of known values
    known = [(i, v) for i, v in enumerate(vals) if v is not None]
    if not known:
        continue  # Skip columns with no data at all
    # Fill leading gaps (before first known value)
    first_known_idx, first_known_val = known[0]
    for i in range(first_known_idx):
        vals[i] = first_known_val
    # Interpolate between known points
    for j in range(len(known) - 1):
        i0, v0 = known[j]
        i1, v1 = known[j + 1]
        gap = i1 - i0
        if gap > 1:
            for i in range(i0 + 1, i1):
                t = (i - i0) / gap
                vals[i] = v0 + (v1 - v0) * t
    # Fill trailing gaps (after last known value)
    last_known_idx, last_known_val = known[-1]
    for i in range(last_known_idx + 1, len(vals)):
        vals[i] = last_known_val
    # Write back
    for i, p in enumerate(parsed):
        p[k] = vals[i]

print("[2] Missing values interpolated.")

# ──────────────────────────────────────────────────────────────────────
# 3.  REMOVE DUPLICATES
# ──────────────────────────────────────────────────────────────────────
seen_years = set()
deduped = []
for p in parsed:
    if p['year'] not in seen_years:
        seen_years.add(p['year'])
        deduped.append(p)
print(f"[3] Duplicates removed: {len(parsed) - len(deduped)}")

# ──────────────────────────────────────────────────────────────────────
# 4.  NORMALISE FORMATS
# ──────────────────────────────────────────────────────────────────────
for p in deduped:
    for k in NUMERIC_COLS:
        p[k] = round(p[k], 3)
print("[4] Numeric values rounded to 3 decimal places.")

# ──────────────────────────────────────────────────────────────────────
# 5.  INTERNAL CONSISTENCY
# ──────────────────────────────────────────────────────────────────────
# Recalculate fossil_fuel_share_pct = 100 - renewable_share_pct
# Validate source_sum <= total (non-energy uses counted in total)
issues = 0
for p in deduped:
    p['fossil_fuel_share_pct'] = round(100.0 - p['renewable_share_pct'], 3)
    src_sum = (p['hydro_twh'] + p['wind_twh'] + p['solar_twh'] + p['biomass_twh']
               + p['nuclear_twh'] + p['coal_twh'] + p['gas_twh'] + p['oil_twh'])
    total = p['total_energy_consumption_twh']
    if src_sum > total * 1.05:
        issues += 1
if issues:
    print(f"[5] WARNING: {issues} years where source sum > total + 5%.")
else:
    print("[5] Consistency checks passed.")

# ──────────────────────────────────────────────────────────────────────
# 6.  OUTLIER DETECTION (IQR)
# ──────────────────────────────────────────────────────────────────────
outlier_count = 0
for col in ['co2_emissions_mt', 'energy_intensity', 'total_energy_consumption_twh']:
    vals = sorted([p[col] for p in deduped])
    n = len(vals)
    q1 = vals[n // 4]
    q3 = vals[3 * n // 4]
    iqr = q3 - q1
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr
    for p in deduped:
        if p[col] < lo or p[col] > hi:
            outlier_count += 1
print(f"[6] Outliers flagged (IQR): {outlier_count}  (expected 0 for smooth series)")

# ──────────────────────────────────────────────────────────────────────
# 7.  YEAR VALIDATION
# ──────────────────────────────────────────────────────────────────────
years = [p['year'] for p in deduped]
year_range_ok = min(years) == 1900 and max(years) == 2024 and len(years) == 125
print(f"[7] Year range [1900, 2024]: {'OK' if year_range_ok else 'ISSUE'}")

# ──────────────────────────────────────────────────────────────────────
# 8.  DERIVED COLUMNS
# ──────────────────────────────────────────────────────────────────────
for p in deduped:
    p['co2_per_capita_t'] = round(p['co2_emissions_mt'] * 1e6 / p['population'], 3)
    p['decade'] = f"{p['year'] // 10 * 10}s"
    p['total_renewable_twh'] = round(p['hydro_twh'] + p['wind_twh'] + p['solar_twh'] + p['biomass_twh'], 3)
    p['total_fossil_twh'] = round(p['coal_twh'] + p['gas_twh'] + p['oil_twh'], 3)
print("[8] Derived columns added.")

# ──────────────────────────────────────────────────────────────────────
# 9.  WRITE FINAL
# ──────────────────────────────────────────────────────────────────────
FIELDNAMES_FINAL = [
    'year', 'energy_source', 'total_energy_consumption_twh',
    'renewable_share_pct', 'fossil_fuel_share_pct', 'co2_emissions_mt',
    'co2_per_capita_t',
    'hydro_twh', 'wind_twh', 'solar_twh', 'biomass_twh', 'nuclear_twh',
    'coal_twh', 'gas_twh', 'oil_twh',
    'total_renewable_twh', 'total_fossil_twh',
    'energy_intensity', 'gdp_usd', 'population',
    'decade', 'policy_event_flag',
]

out_path = os.path.join(IN_DIR, 'austria_energy_final.csv')
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES_FINAL)
    writer.writeheader()
    for p in deduped:
        writer.writerow({k: p[k] for k in FIELDNAMES_FINAL})

print(f"[9] Written: {out_path}  ({len(deduped)} rows, {len(FIELDNAMES_FINAL)} cols)")
print("data_cleaning.py completed.")
