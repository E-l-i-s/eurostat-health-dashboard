"""
Generate dml_populate_data.sql from austria_energy_final.csv.
Reads the CSV, normalizes into 8 tables, and writes INSERT statements.
"""

import csv

CSV_PATH = r"C:\Users\elisa\Desktop\KEMV-FINALFINAL\Austria_Energy_Capstone\Capstone1\austria_energy_final.csv"
OUT_PATH = r"C:\Users\elisa\Desktop\KEMV-FINALFINAL\Austria_Energy_Capstone\Capstone2\dml_populate_data.sql"

with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# --- Build lookup sets ---
distinct_sources = set()
for r in rows:
    distinct_sources.add(r["energy_source"].strip())

# Map source -> source_id
source_ids = {s: i + 1 for i, s in enumerate(sorted(distinct_sources))}

# Map source -> category
source_category = {
    "coal": "Fossil",
    "oil": "Fossil",
    "gas": "Fossil",
    "hydro": "Renewable",
}

# year -> year_id
years = sorted({int(r["year"]) for r in rows})
year_ids = {y: i + 1 for i, y in enumerate(years)}

# decade list
decades = sorted({r["decade"].strip() for r in rows})

# Austria
country_id = 1

lines = []
lines.append("-- =============================================================================")
lines.append("-- DML: Austria Energy Transition Capstone 2")
lines.append("-- Populates all tables from austria_energy_final.csv")
lines.append("-- =============================================================================")
lines.append("")
lines.append("BEGIN;")
lines.append("")

# --- country ---
lines.append("-- country")
lines.append("INSERT INTO country (country_id, country_name, country_code, region)")
lines.append("VALUES (1, 'Austria', 'AUT', 'Central Europe');")
lines.append("")

# --- year_dim ---
lines.append("-- year_dim")
lines.append("INSERT INTO year_dim (year_id, year, decade) VALUES")
decade_for_year = {}
for r in rows:
    y = int(r["year"])
    if y not in decade_for_year:
        decade_for_year[y] = r["decade"].strip()
year_vals = []
for y in years:
    year_vals.append(f"    ({year_ids[y]}, {y}, '{decade_for_year[y]}')")
lines.append(",\n".join(year_vals) + ";")
lines.append("")

# --- energy_source ---
lines.append("-- energy_source")
lines.append("INSERT INTO energy_source (source_id, source_name, category) VALUES")
src_vals = []
for s in sorted(distinct_sources):
    cat = source_category.get(s, "Other")
    src_vals.append(f"    ({source_ids[s]}, '{s}', '{cat}')")
lines.append(",\n".join(src_vals) + ";")
lines.append("")

# --- consumption ---
lines.append("-- consumption")
lines.append("INSERT INTO consumption (consumption_id, year_id, country_id, source_id,")
lines.append("    total_energy_twh, renewable_share_pct, fossil_share_pct,")
lines.append("    total_renewable_twh, total_fossil_twh) VALUES")
c_vals = []
for i, r in enumerate(rows):
    y = int(r["year"])
    sid = source_ids[r["energy_source"].strip()]
    cid = i + 1
    c_vals.append(
        f"    ({cid}, {year_ids[y]}, {country_id}, {sid},"
        f" {r['total_energy_consumption_twh']}, {r['renewable_share_pct']},"
        f" {r['fossil_fuel_share_pct']}, {r['total_renewable_twh']},"
        f" {r['total_fossil_twh']})"
    )
lines.append(",\n".join(c_vals) + ";")
lines.append("")

# --- emissions ---
lines.append("-- emissions")
lines.append("INSERT INTO emissions (emission_id, year_id, country_id,")
lines.append("    co2_emissions_mt, co2_per_capita_t) VALUES")
e_vals = []
for i, r in enumerate(rows):
    y = int(r["year"])
    eid = i + 1
    e_vals.append(
        f"    ({eid}, {year_ids[y]}, {country_id},"
        f" {r['co2_emissions_mt']}, {r['co2_per_capita_t']})"
    )
lines.append(",\n".join(e_vals) + ";")
lines.append("")

# --- electricity_generation ---
lines.append("-- electricity_generation")
lines.append("INSERT INTO electricity_generation (generation_id, year_id, country_id, source_id,")
lines.append("    hydro_twh, wind_twh, solar_twh, biomass_twh, nuclear_twh,")
lines.append("    coal_twh, gas_twh, oil_twh) VALUES")
g_vals = []
for i, r in enumerate(rows):
    y = int(r["year"])
    sid = source_ids[r["energy_source"].strip()]
    gid = i + 1
    g_vals.append(
        f"    ({gid}, {year_ids[y]}, {country_id}, {sid},"
        f" {r['hydro_twh']}, {r['wind_twh']}, {r['solar_twh']}, {r['biomass_twh']},"
        f" {r['nuclear_twh']}, {r['coal_twh']}, {r['gas_twh']}, {r['oil_twh']})"
    )
lines.append(",\n".join(g_vals) + ";")
lines.append("")

# --- policy_event ---
lines.append("-- policy_event")
lines.append("INSERT INTO policy_event (policy_id, year_id, country_id, event_flag, description) VALUES")
p_vals = []
pid = 0
for i, r in enumerate(rows):
    flag = int(r["policy_event_flag"])
    y = int(r["year"])
    if flag == 1:
        pid += 1
        desc = f"'Policy event in {y}'"
        p_vals.append(
            f"    ({pid}, {year_ids[y]}, {country_id}, TRUE, {desc})"
        )
if p_vals:
    lines.append(",\n".join(p_vals) + ";")
else:
    lines.append("    (1, 1, 1, FALSE, 'No policy events');")
lines.append("")

# --- economic_indicator ---
lines.append("-- economic_indicator")
lines.append("INSERT INTO economic_indicator (indicator_id, year_id, country_id,")
lines.append("    gdp_usd, population, energy_intensity) VALUES")
i_vals = []
for i, r in enumerate(rows):
    y = int(r["year"])
    iid = i + 1
    i_vals.append(
        f"    ({iid}, {year_ids[y]}, {country_id},"
        f" {r['gdp_usd']}, {int(float(r['population']))}, {r['energy_intensity']})"
    )
lines.append(",\n".join(i_vals) + ";")
lines.append("")

lines.append("COMMIT;")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Generated: {OUT_PATH}")
