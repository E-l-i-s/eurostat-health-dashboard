# Data Collection Strategy

## Method: Eurostat REST API (JSON:stat Format)

I retrieve all data programmatically from the Eurostat API at `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/`. The API returns data in JSON:stat format, a statistical data interchange standard that encodes dimensional data as a sparse array. This method is preferred over manual CSV download because it guarantees reproducibility — the Python script specifies exact dimension filters and retrieves exactly the same data on every execution, eliminating manual selection errors and enabling straightforward re-execution when Eurostat updates its data.

## Alternative Method: Manual CSV Download

As an alternative, each dataset can be downloaded manually through the Eurostat Data Browser:
1. Navigate to the dataset URL
2. Select desired dimensions (sex, age, condition type, geography)
3. Select the "CSV" export option
4. Save the file to the project directory

The API approach is superior because it eliminates the 30+ manual clicks required per dataset, embeds the retrieval parameters in documented code, and supports automated re-retrieval for updates.

## Frequency and Timing

One-time batch retrieval covering all three EHIS waves (2008, 2014, 2019). The script retrieves all available years from the API without hardcoding year values, ensuring that any Eurostat data revisions or additions are captured automatically.

## Tools

- Python 3.10+
- `requests` library for HTTP calls
- `pandas` for data manipulation
- `json` (stdlib) for JSON:stat parsing
- `sqlite3` (stdlib) for database loading in Capstone 2

## Storage Pipeline

```
Eurostat API → Raw JSON (saved to disk) → Parsed DataFrame → CSV export → SQLite database (Capstone 2)
```

Each raw API response is saved before any processing: `raw_pe3.json`, `raw_cd1e.json`, `raw_bm1e.json`. This preserves the original response for audit and re-parsing. Parsing transforms JSON:stat sparse arrays into normalized pandas DataFrames. The three DataFrames are concatenated into a single uncleaned CSV. The cleaned version feeds the database in Capstone 2.

## Merge Strategy

The composite key for record identity is:

```
(geo, time, sex, age, indicator_code)
```

This composite key is necessary because:
- `geo` alone identifies only the country — multiple indicators, years, sexes, and age groups exist per country
- Adding `time` resolves survey waves but not demographic or indicator distinctions
- Adding `sex` and `age` isolates specific demographic groups
- Adding `indicator_code` distinguishes between different health measures (activity vs. specific chronic conditions)

Without all five components, a single row cannot be uniquely identified.

## Data Volume Justification

Approximate dimension cardinalities:
- Country codes: ~35
- Age groups: 8 (TOTAL, Y18-24, Y25-34, Y35-44, Y45-54, Y55-64, Y65-74, Y75+)
- Sex categories: 3 (Total, Male, Female)
- Survey waves: 3 (2008, 2014, 2019)
- Indicator variations: ~10 (physical activity + 4 chronic conditions + BMI categories)

**Calculation:** 35 × 8 × 3 × 3 × 10 = 25,200 potential rows. Not all combinations exist in the data (Eurostat suppresses small-cell counts), but the dataset reliably exceeds 10,000 rows across the three combined sources.
