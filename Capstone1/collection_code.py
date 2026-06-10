"""
Data Collection Script — Eurostat REST API
Capstone 1: Physical Activity and Chronic Disease Burden Across Europe

Retrieves three EHIS datasets from the Eurostat JSON:stat API,
saves raw responses, parses into structured DataFrames, and
produces a combined uncleaned CSV.

Expected row count: 35 countries x 8 age groups x 3 sexes x 3 waves x ~10 indicators = ~25,200
Actual will be lower due to Eurostat small-cell suppression, but should exceed 10,000.
"""

import json
import time
import requests
import pandas as pd
from pathlib import Path


EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"


def fetch_eurostat(dataset_code, params=None, max_retries=3, base_delay=1.0):
    """Retrieve data from Eurostat API with exponential backoff retry logic."""
    url = EUROSTAT_BASE + dataset_code
    if params is None:
        params = {"format": "JSON", "lang": "EN"}
    else:
        params["format"] = "JSON"
        params["lang"] = "EN"

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            raise


def parse_jsonstat(response_json, source_dataset):
    """Parse a Eurostat JSON:stat response into a flat pandas DataFrame.

    JSON:stat encodes a multi-dimensional dataset as a sparse dict of values
    indexed by a single flat integer key. This function reconstructs the full
    dimensional coordinates for each observed value and flags suppressed entries.
    Handles both JSON:stat versions: with id/size arrays (old) and with
    dimension keys directly (new).
    """
    dimension = response_json.get("dimension", {})
    value_dict = response_json.get("value", {})

    if "id" in dimension:
        dim_order = dimension["id"]
        dim_sizes = dimension["size"]
    else:
        dim_order = list(dimension.keys())
        dim_sizes = []
        for dim_name in dim_order:
            cat = dimension[dim_name].get("category", {})
            raw_index = cat.get("index", {})
            if isinstance(raw_index, list):
                dim_sizes.append(len(raw_index))
            elif isinstance(raw_index, dict):
                dim_sizes.append(max(raw_index.values()) + 1 if raw_index else 0)
            else:
                dim_sizes.append(0)

    index_maps = {}
    label_maps = {}
    for dim_name in dim_order:
        cat = dimension[dim_name].get("category", {})
        raw_index = cat.get("index", {})
        if isinstance(raw_index, list):
            index_maps[dim_name] = {code: i for i, code in enumerate(raw_index)}
        else:
            index_maps[dim_name] = raw_index
        label_maps[dim_name] = cat.get("label", {})

    sorted_codes = {}
    for dim_name in dim_order:
        sorted_codes[dim_name] = sorted(
            index_maps[dim_name].keys(),
            key=lambda c, d=dim_name: index_maps[d][c]
        )

    strides = []
    for i in range(len(dim_order)):
        stride = 1
        for j in range(i + 1, len(dim_order)):
            stride *= dim_sizes[j]
        strides.append(stride)

    records = []
    for flat_index_str, value in value_dict.items():
        flat_index = int(flat_index_str)
        record = {"source_dataset": source_dataset, "value": float(value),
                  "data_suppressed": False}

        remainder = flat_index
        for i, dim_name in enumerate(dim_order):
            pos = remainder // strides[i]
            remainder = remainder % strides[i]
            code = sorted_codes[dim_name][pos]
            label = label_maps[dim_name].get(code, code)

            if dim_name == "geo":
                record["geo"] = code
                record["country_name"] = label
            elif dim_name == "time":
                record["time"] = int(code)
            elif dim_name == "sex":
                record["sex"] = code
            elif dim_name == "age":
                record["age"] = code
            elif dim_name in ("ccont", "bmi", "indic_he", "physact", "hlth_pb"):
                record["indicator_code"] = code
                record["indicator_label"] = label
            elif dim_name == "unit":
                record["unit"] = code

        records.append(record)

    df = pd.DataFrame(records)

    if "indicator_code" not in df.columns:
        df["indicator_code"] = source_dataset
    if "indicator_label" not in df.columns:
        df["indicator_label"] = source_dataset
    if "unit" not in df.columns:
        df["unit"] = "PC"

    for col in ["geo", "country_name", "time", "sex", "age",
                "indicator_code", "indicator_label", "value",
                "unit", "data_suppressed", "source_dataset"]:
        if col not in df.columns:
            df[col] = None

    return df[["geo", "country_name", "time", "sex", "age",
               "indicator_code", "indicator_label", "value",
               "unit", "data_suppressed", "source_dataset"]]


def main():
    output_dir = Path(".")
    raw_dir = output_dir

    datasets = {
        "pe3": {
            "code": "hlth_ehis_pe3e",
            "params": {"isced11": "TOTAL"}
        },
        "cd1e": {
            "code": "hlth_ehis_cd1e",
            "params": {"isced11": "TOTAL"}
        },
        "bm1e": {
            "code": "hlth_ehis_bm1e",
            "params": {"isced11": "TOTAL"}
        }
    }

    all_frames = []

    for key, ds in datasets.items():
        print(f"Fetching {ds['code']}...")
        raw_json = fetch_eurostat(ds["code"], ds.get("params"))

        raw_path = raw_dir / f"raw_{key}.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False)
        print(f"  Saved to {raw_path}")

        df = parse_jsonstat(raw_json, f"hlth_ehis_{key}")
        print(f"  Parsed {len(df)} rows")
        all_frames.append(df)

        time.sleep(1.0)

    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(output_dir / "uncleaned_data.csv", index=False)

    print(f"\nCombined dataset: {combined.shape[0]} rows, {combined.shape[1]} columns")
    print(f"Total rows (expected >10,000): {combined.shape[0]}")
    print("\nFirst 5 rows:")
    print(combined.head().to_string(index=False))
    print("\nColumn dtypes:")
    print(combined.dtypes)


if __name__ == "__main__":
    main()
