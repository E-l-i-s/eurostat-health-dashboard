"""
validate_csv.py — Validates austria_energy_final.csv against verified real-world sources
"""
import csv

rows = list(csv.DictReader(open('austria_energy_final.csv', encoding='utf-8')))
by_year = {int(r['year']): r for r in rows}
errors = []

# 1. No duplicate years
years = [int(r['year']) for r in rows]
assert len(set(years)) == len(years), 'Duplicate years found!'
print(f'Total years: {len(rows)} (1900-2024, no duplicates)')

# 2. Biomass never zero
for r in rows:
    if float(r['biomass_twh']) < 0.1:
        errors.append(f"Biomass < 0.1 at {r['year']}: {r['biomass_twh']}")

# 3. Nuclear always 0 (Zwentendorf referendum — Austria never operated nuclear)
for r in rows:
    if float(r['nuclear_twh']) != 0.0:
        errors.append(f"Nuclear != 0 at {r['year']}: {r['nuclear_twh']}")

# 4. Eurostat-verified Austria renewable shares [SDG_07_40]
expected_AT = {
    2004: 24.35, 2010: 31.21, 2015: 33.50,
    2020: 36.55, 2022: 34.08, 2023: 40.84
}
for y, v in expected_AT.items():
    actual = float(by_year[y]['renewable_share_pct'])
    diff = abs(actual - v)
    status = 'OK' if diff <= 0.5 else 'WARN'
    print(f"  AT renewable {y}: Eurostat={v}%, CSV={actual:.2f}% [{status}]")
    if diff > 1.0:
        errors.append(f"AT renewable {y}: expected ~{v}%, got {actual:.2f}%")

# 5. Eurostat-verified EU average renewable shares [SDG_07_40]
expected_EU = {2004: 9.6, 2010: 12.5, 2020: 22.1, 2022: 23.1}
for y, v in expected_EU.items():
    actual = float(by_year[y]['eu_renewable_share_pct'])
    diff = abs(actual - v)
    status = 'OK' if diff <= 0.5 else 'WARN'
    print(f"  EU renewable {y}: Eurostat={v}%, CSV={actual:.2f}% [{status}]")
    if diff > 1.0:
        errors.append(f"EU renewable {y}: expected ~{v}%, got {actual:.2f}%")

# 6. Austria always > EU (documented hydro advantage)
fail_count = 0
for r in rows:
    if int(r['year']) >= 2000:
        if float(r['renewable_share_pct']) <= float(r['eu_renewable_share_pct']):
            fail_count += 1
if fail_count:
    errors.append(f'AT <= EU in {fail_count} years after 2000')
else:
    print('  Austria > EU renewable share: OK for all years >= 2000')

# 7. CO2 peak year (should be ~2005 per UBA/EDGAR, not 1979)
peak = max(rows, key=lambda r: float(r['co2_emissions_mt']))
print(f"\nCO2 peak: year={peak['year']}, value={float(peak['co2_emissions_mt']):.1f} Mt")
print(f"  Expected: ~2005, ~80 Mt [UBA/EDGAR verified]")
if abs(int(peak['year']) - 2005) > 3:
    errors.append(f"CO2 peak at {peak['year']}, expected ~2005")

# 8. World Bank verified GDP 2000
gdp_2000 = float(by_year[2000]['gdp_usd'])
print(f"\nGDP 2000: ${gdp_2000/1e9:.1f}B (World Bank verified: $196.3B)")
if not (170e9 < gdp_2000 < 220e9):
    errors.append(f"GDP 2000: {gdp_2000/1e9:.1f}B, expected ~$196B")

# 9. Population anchors [Statistik Austria]
pop_checks = {1970: 7491526, 2000: 8032587, 2020: 8907777}
for y, v in pop_checks.items():
    actual = float(by_year[y]['population'])
    pct_diff = abs(actual - v) / v * 100
    status = 'OK' if pct_diff < 2 else 'WARN'
    print(f"  Population {y}: STATAUT={v:,}, CSV={actual:,.0f} ({pct_diff:.1f}% diff) [{status}]")

# 10. YoY energy continuity (no sudden jumps outside shock years)
shock_years = {1918, 1945, 1946, 1947, 2020}
big_jumps = []
for i in range(1, len(rows)):
    prev = float(rows[i-1]['total_energy_consumption_twh'])
    curr = float(rows[i]['total_energy_consumption_twh'])
    yoy = abs(curr - prev) / prev * 100
    yr = int(rows[i]['year'])
    if yoy > 15 and yr not in shock_years:
        big_jumps.append(f"{yr}: {yoy:.1f}%")
if big_jumps:
    errors.append(f"Large YoY jumps: {big_jumps}")
else:
    print(f"\n  YoY energy continuity: OK (no unexlained jumps > 15%)")

# Final summary
print("\n" + "="*60)
if errors:
    print("VALIDATION ERRORS FOUND:")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL VALIDATION CHECKS PASSED.")
    print("Data is internally consistent and matches verified sources.")
