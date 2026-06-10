"""
Database Population Script — Capstone 2
Reads cleaned_data.csv and populates the capstone.db SQLite database
with 8 tables (6 dimension + 1 fact + 1 bridge) per the star schema.
"""

import sqlite3
import csv
from pathlib import Path


DB_PATH = Path(__file__).parent / "capstone.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DATA_PATH = Path(__file__).parent.parent / "Capstone1" / "cleaned_data.csv"


def create_tables(conn):
    """Execute schema.sql to create all database tables."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def populate_dimensions(conn, rows):
    """Populate dimension tables from cleaned data rows."""
    cur = conn.cursor()

    # Country
    countries = {}
    for r in rows:
        geo = r["geo"]
        if geo and geo not in countries:
            countries[geo] = {
                "code": geo,
                "name": r.get("country_name", geo),
                "region": classify_region(geo)
            }
    for c in countries.values():
        cur.execute(
            "INSERT OR IGNORE INTO Country (country_code, country_name, region) VALUES (?, ?, ?)",
            (c["code"], c["name"], c["region"])
        )

    # AgeGroup
    age_groups = {}
    for r in rows:
        ag = r.get("age_group", "")
        if ag and ag not in age_groups:
            age_groups[ag] = {
                "code": ag,
                "label": ag.replace("Y", "").replace("-", "–").replace("_GE", "+").replace("_LT", "<"),
                "lower": parse_age_bound(ag, "lower"),
                "upper": parse_age_bound(ag, "upper")
            }
    for a in age_groups.values():
        cur.execute(
            "INSERT OR IGNORE INTO AgeGroup (age_code, label, lower_bound, upper_bound) VALUES (?, ?, ?, ?)",
            (a["code"], a["label"], a["lower"], a["upper"])
        )

    # Sex
    sexes = {"T": "Total", "M": "Male", "F": "Female"}
    for code, label in sexes.items():
        cur.execute(
            "INSERT OR IGNORE INTO Sex (sex_code, label) VALUES (?, ?)",
            (code, label)
        )

    # IndicatorCategory
    categories_seen = set()
    for r in rows:
        cat = r.get("indicator_category", "")
        if cat and cat not in categories_seen:
            categories_seen.add(cat)
            cat_code = cat.lower().replace(" ", "_")
            cur.execute(
                "INSERT OR IGNORE INTO IndicatorCategory (category_code, category_name) VALUES (?, ?)",
                (cat_code, cat)
            )

    # DataSource
    sources_seen = set()
    for r in rows:
        src = r.get("source_dataset", "")
        if src and src not in sources_seen:
            sources_seen.add(src)
            cur.execute(
                "INSERT OR IGNORE INTO DataSource (source_code, full_name, api_endpoint, retrieval_date) VALUES (?, ?, ?, date('now'))",
                (src, f"Eurostat {src}", f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{src}",)
            )

    # HealthIndicator
    indicators_seen = set()
    for r in rows:
        ic = r.get("indicator_code", "")
        if ic and ic not in indicators_seen:
            indicators_seen.add(ic)
            cat = r.get("indicator_category", "").lower().replace(" ", "_")
            src = r.get("source_dataset", "")
            cur.execute(
                "INSERT OR IGNORE INTO HealthIndicator (indicator_code, indicator_label, category_code, source_code, unit_of_measure) VALUES (?, ?, ?, ?, ?)",
                (ic, r.get("indicator_label", ic), cat, src, r.get("unit", "PC"))
            )

    conn.commit()
    print("Dimension tables populated.")


def populate_measurements(conn, rows):
    """Populate the Measurement fact table."""
    cur = conn.cursor()

    wave_map = {"2008": 2008, "2014": 2014, "2019": 2019}

    inserted = 0
    for r in rows:
        try:
            value = float(r["value"])
        except (ValueError, TypeError):
            continue
        time_val = r.get("time", "")
        if time_val and str(time_val).isdigit():
            wave = int(time_val)
        else:
            continue

        suppressed = 1 if str(r.get("data_suppressed", "False")).lower() in ("true", "1") else 0
        outlier = 1 if str(r.get("is_outlier_flagged", "False")).lower() in ("true", "1") else 0
        geo = r.get("geo", "")
        age = r.get("age_group", "")
        sex = r.get("sex", "")
        # Map sex back to code
        sex_map = {"Total": "T", "Male": "M", "Female": "F"}
        sex_code = sex_map.get(sex)
        if sex_code is None:
            print(f"  Warning: unrecognized sex value '{sex}' — skipping row")
            continue
        indicator = r.get("indicator_code", "")

        if not all([geo, age, indicator]):
            continue

        cur.execute(
            """INSERT INTO Measurement
               (country_code, age_code, sex_code, indicator_code, wave_id, value, data_suppressed, is_outlier)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (geo, age, sex_code, indicator, wave, value, suppressed, outlier)
        )
        inserted += 1

    conn.commit()
    print(f"Measurement fact table: {inserted} rows inserted.")


def classify_region(geo_code):
    """Classify a country code into a European region."""
    northern = {"DK", "FI", "IS", "NO", "SE", "EE", "LV", "LT"}
    western = {"AT", "BE", "FR", "DE", "LI", "LU", "MC", "NL", "CH", "UK"}
    southern = {"HR", "GR", "IT", "MT", "PT", "SI", "ES", "AD", "CY", "EL"}
    eastern = {"BG", "CZ", "HU", "PL", "RO", "SK", "AL", "BA", "ME", "MK", "RS", "TR", "XK"}
    if geo_code in northern:
        return "Northern Europe"
    if geo_code in western:
        return "Western Europe"
    if geo_code in southern:
        return "Southern Europe"
    if geo_code in eastern:
        return "Eastern Europe"
    return "Other"


def parse_age_bound(age_code, bound_type):
    """Extract lower or upper bound from age group code."""
    age_code = age_code.upper()
    if age_code == "TOTAL":
        return None
    age_code = age_code.replace("Y", "")
    if "_GE" in age_code:
        parts = age_code.split("_GE")
        lower = int(parts[1]) if parts[1].isdigit() else None
        return lower if bound_type == "lower" else None
    if "_LT" in age_code:
        parts = age_code.split("_LT")
        upper = int(parts[1]) if parts[1].isdigit() else None
        return None if bound_type == "lower" else upper
    if "-" in age_code:
        parts = age_code.split("-")
        if len(parts) == 2:
            lower = int(parts[0]) if parts[0].isdigit() else None
            upper = int(parts[1]) if parts[1].isdigit() else None
            return lower if bound_type == "lower" else upper
    return None


def print_row_counts(conn):
    """Print row counts for all 8 tables."""
    cur = conn.cursor()
    tables = ["Country", "AgeGroup", "Sex", "IndicatorCategory", "DataSource",
              "HealthIndicator", "SurveyWave", "Measurement"]
    print("\n--- Row Counts ---")
    total = 0
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count} rows")
        total += count
    print(f"  TOTAL: {total} rows across {len(tables)} tables")


def main():
    if not DATA_PATH.exists():
        print(f"cleaned_data.csv not found at {DATA_PATH}")
        print("Run the Capstone 1 cleaning script first.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    create_tables(conn)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} rows from cleaned_data.csv")

    populate_dimensions(conn, rows)
    populate_measurements(conn, rows)

    # Insert survey waves
    cur = conn.cursor()
    waves = [(2008, "EHIS Wave 1 (2008)", 2008),
             (2014, "EHIS Wave 2 (2014)", 2014),
             (2019, "EHIS Wave 3 (2019)", 2019)]
    for w_id, desc, yr in waves:
        cur.execute(
            "INSERT OR IGNORE INTO SurveyWave (wave_id, description, year) VALUES (?, ?, ?)",
            (w_id, desc, yr)
        )
    conn.commit()

    print_row_counts(conn)

    # Sample query verification
    print("\n--- Sample: Measurement joined to Country and HealthIndicator ---")
    cur.execute("""
        SELECT m.measurement_id, c.country_name, hi.indicator_label,
               m.value, m.wave_id
        FROM Measurement m
        JOIN Country c ON m.country_code = c.country_code
        JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row}")

    conn.close()
    print(f"\nDatabase saved to {DB_PATH}")


if __name__ == "__main__":
    main()
