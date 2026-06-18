"""Quick smoke test for all API endpoints."""
import urllib.request, json

ENDPOINTS = [
    ('energy_mix',      'http://127.0.0.1:5000/api/energy_mix?min_year=1970&max_year=2024'),
    ('renewable_share', 'http://127.0.0.1:5000/api/renewable_share'),
    ('co2_decade',      'http://127.0.0.1:5000/api/co2_decade'),
    ('kpi_summary',     'http://127.0.0.1:5000/api/kpi_summary'),
    ('compare_eu',      'http://127.0.0.1:5000/api/compare_eu?min_year=2000&max_year=2024'),
    ('annual_stats',    'http://127.0.0.1:5000/api/annual_stats'),
    ('sankey',          'http://127.0.0.1:5000/api/sankey'),
    ('heatmap',         'http://127.0.0.1:5000/api/heatmap'),
    ('intensity_vs_gdp','http://127.0.0.1:5000/api/intensity_vs_gdp'),
    ('renewable_growth','http://127.0.0.1:5000/api/renewable_growth'),
]

all_ok = True
for name, url in ENDPOINTS:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())

            if name == 'annual_stats':
                row2005 = next((d for d in data if d['year'] == 2005), None)
                co2 = row2005['co2_emissions_mt'] if row2005 else 0
                src = row2005['energy_source'] if row2005 else 'N/A'
                print(f"  OK {name}: 2005 CO2={co2:.1f}Mt dominant={src} ({len(data)} rows)")

            elif name == 'compare_eu':
                at = data['austria'][-1]
                eu = data['eu_average'][-1]
                gap = at['renewable_share'] - eu['renewable_share']
                print(f"  OK {name}: 2024 AT={at['renewable_share']:.1f}%  EU={eu['renewable_share']:.1f}%  gap={gap:.1f}pp")
                if gap < 5:
                    print("  WARNING: AT-EU gap < 5pp — check EU series independence!")
                    all_ok = False

            elif name == 'sankey':
                print(f"  OK {name}: {len(data['flows'])} flows, year={data['year']}")

            elif name == 'kpi_summary':
                print(f"  OK {name}: share={data['current_renewable_share']}%  CO2red={data['co2_reduction_pct']}%  peak_yr={data['peak_co2_year']}")
                if data['peak_co2_year'] != 2005:
                    print(f"  WARNING: peak CO2 year = {data['peak_co2_year']}, expected 2005!")
                    all_ok = False

            elif name == 'renewable_share':
                policies = data.get('policies', [])
                zwent = any(p['year'] == 1978 for p in policies)
                print(f"  OK {name}: {len(data['years'])} years, {len(policies)} policy events, Zwentendorf 1978={'YES' if zwent else 'MISSING!'}")
                if not zwent:
                    all_ok = False

            elif name == 'heatmap':
                print(f"  OK {name}: {len(data['decades'])} decades x {len(data['sources'])} sources")

            elif isinstance(data, list):
                first_yr = data[0]['year'] if data else 'N/A'
                last_yr  = data[-1]['year'] if data else 'N/A'
                print(f"  OK {name}: {len(data)} rows ({first_yr}–{last_yr})")

            else:
                print(f"  OK {name}: keys={list(data.keys())[:5]}")

    except Exception as ex:
        print(f"  FAIL {name}: {ex}")
        all_ok = False

print()
print("RESULT:", "ALL ENDPOINTS PASSED" if all_ok else "SOME WARNINGS — see above")
