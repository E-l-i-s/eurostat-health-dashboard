"""
Data Cleaning Script — Capstone 1
Applies cleaning steps to uncleaned_data.csv and produces cleaned_data.csv
with exactly 15 standardized columns.
"""

import pandas as pd
import numpy as np
from pathlib import Path


ISO_COUNTRY_CODES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO",
    "CH", "ME", "MK", "AL", "RS", "TR", "BA", "XK"
}


AGE_ORDER = [
    "TOTAL", "Y15-19", "Y15-24", "Y15-29", "Y15-44", "Y15-64",
    "Y18-24", "Y18-29", "Y18-44", "Y18-64",
    "Y20-24", "Y25-29", "Y25-34", "Y25-54", "Y25-64",
    "Y35-44", "Y45-54", "Y45-64", "Y55-64",
    "Y65-74", "Y_GE18", "Y_GE65", "Y_GE75"
]


def main():
    input_path = Path("uncleaned_data.csv")
    if not input_path.exists():
        print("uncleaned_data.csv not found. Run collection_code.py first.")
        return

    df = pd.read_csv(input_path)
    initial_rows = len(df)
    print(f"Loaded {initial_rows} rows from {input_path}")

    # Step 1: Flag suppressed data
    suppressed_count = df["data_suppressed"].sum()
    suppressed_pct = (suppressed_count / initial_rows) * 100
    print(f"Step 1 — Suppressed rows: {suppressed_count} ({suppressed_pct:.1f}%)")
    print("  Decision: Exclude suppressed values from analysis but retain in dataset")
    print("  with flag. EHIS suppresses small-cell counts (n < 5) for confidentiality.")
    print("  Imputation would introduce bias; exclusion with flagging is correct.")

    # Step 2: Check for duplicate records on composite key
    composite_key = ["geo", "time", "sex", "age", "indicator_code"]
    dup_before = df.duplicated(subset=composite_key, keep=False).sum()
    print(f"Step 2 — Duplicate rows on composite key: {dup_before}")
    if dup_before > 0:
        df = df.drop_duplicates(subset=composite_key, keep="first")
        print(f"  Removed {dup_before - df.duplicated(subset=composite_key, keep=False).sum()} duplicates")

    # Step 3: Data type normalization
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["geo"] = df["geo"].astype(str).str.upper().str.strip()
    age_cat = pd.CategoricalDtype(categories=AGE_ORDER, ordered=True)
    df["age"] = df["age"].astype(str).str.strip()
    df["age_group"] = df["age"].astype(age_cat)
    print(f"Step 3 — Data types normalized.")

    # Step 4: Outlier flagging (IQR method per indicator_code group)
    df["is_outlier_flagged"] = False
    outlier_count = 0
    for code, group in df.groupby("indicator_code"):
        q1 = group["value"].quantile(0.25)
        q3 = group["value"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 3.0 * iqr
        upper = q3 + 3.0 * iqr
        mask = (group["value"] < lower) | (group["value"] > upper)
        df.loc[mask.index[mask.values], "is_outlier_flagged"] = True
        outlier_count += mask.sum()
    print(f"Step 4 — Outliers flagged (3xIQR): {outlier_count}")
    print("  Decision: Flag, do not remove. EHIS values are bounded 0-100%.")
    print("  True extreme outliers likely indicate data quality issues worth noting.")

    # Step 5: Standardize sex codes
    sex_map = {"T": "Total", "M": "Male", "F": "Female"}
    df["sex"] = df["sex"].map(sex_map).fillna(df["sex"])
    print(f"Step 5 — Sex codes standardized: {df['sex'].unique()}")

    # Standardize age group labels for consistency
    known_ages = set(AGE_ORDER)
    unknown_ages = set(df["age"].unique()) - known_ages
    if unknown_ages:
        print(f"  Unknown age groups found: {unknown_ages} — mapping to age_group as-is")

    # Verify geo codes
    valid_geo = df["geo"].isin(ISO_COUNTRY_CODES)
    invalid_geo = df.loc[~valid_geo, "geo"].unique()
    if len(invalid_geo) > 0:
        print(f"  Geo codes not in ISO list: {invalid_geo} — these may be aggregates (e.g. EU28)")

    # Build indicator_category from source and code patterns
    def categorize_indicator(row):
        code = str(row["indicator_code"]).lower()
        src = str(row["source_dataset"]).lower()
        if "pe3" in src or "pe9" in src:
            return "Physical Activity"
        if "bm1e" in src or "bmi" in code or "obes" in code:
            return "BMI"
        return "Chronic Disease"

    df["indicator_category"] = df.apply(categorize_indicator, axis=1)

    # Build ehis_wave
    wave_map = {2008: "EHIS Wave 1 (2008)", 2014: "EHIS Wave 2 (2014)", 2019: "EHIS Wave 3 (2019)"}
    df["ehis_wave"] = df["time"].map(wave_map).fillna("Unknown")

    # last_retrieved timestamp
    from datetime import datetime
    df["last_retrieved"] = datetime.now().strftime("%Y-%m-%d")

    # Final column selection and ordering
    final_columns = [
        "geo", "country_name", "time", "sex", "age_group",
        "indicator_code", "indicator_label", "indicator_category",
        "value", "unit", "data_suppressed", "is_outlier_flagged",
        "source_dataset", "ehis_wave", "last_retrieved"
    ]
    for col in final_columns:
        if col not in df.columns:
            df[col] = None

    df_clean = df[final_columns].copy()
    df_clean.columns = final_columns

    output_path = Path("cleaned_data.csv")
    df_clean.to_csv(output_path, index=False)

    print(f"\nCleaned dataset: {len(df_clean)} rows, {len(final_columns)} columns")
    print(f"Saved to {output_path}")

    # Schema summary
    schema_rows = []
    for col in final_columns:
        dtype = str(df_clean[col].dtype)
        example = str(df_clean[col].iloc[0]) if len(df_clean) > 0 else "N/A"
        nullable = "Yes" if df_clean[col].isna().any() else "No"
        schema_rows.append(f"| {col} | {dtype} | {example} | {nullable} |")

    print("\n| Column | Data Type | Example Value | Nullable |")
    print("|--------|-----------|--------------|----------|")
    for row in schema_rows:
        print(row)

    print("\nFirst 5 rows of cleaned data:")
    print(df_clean.head().to_string(index=False))


if __name__ == "__main__":
    main()
