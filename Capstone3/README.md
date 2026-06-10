# Physical Activity and Chronic Disease Burden Across Europe

## Interactive Dashboards for Public Health Research

Three interconnected capstone projects analyzing Eurostat EHIS survey data on physical activity insufficiency and chronic disease prevalence across 35 European countries. The research quantifies the relationship between inactivity rates and chronic conditions (obesity, diabetes, hypertension, cardiovascular disease), identifies high-burden countries, and provides two interactive dashboards communicating these findings to policymakers and researchers.

## Setup Instructions

```bash
# 1. Install the single required dependency
pip install flask

# 2. Populate the SQLite database from cleaned data
cd Capstone2
python populate_db.py

# 3. Launch the dashboard server
cd ../Capstone3
python app.py
```

## Accessing the Dashboards

Once the server is running (default http://127.0.0.1:5000):

- **Dashboard 1 (Strategic):** http://127.0.0.1:5000/
- **Dashboard 2 (Analytical):** http://127.0.0.1:5000/analytics

## Data Sources

- **Physical activity (hlth_ehis_pe3):** https://ec.europa.eu/eurostat/databrowser/view/hlth_ehis_pe3/default/table
- **Chronic conditions (hlth_ehis_cd1e):** https://ec.europa.eu/eurostat/databrowser/view/hlth_ehis_cd1e/default/table
- **BMI classification (hlth_ehis_bm1e):** https://ec.europa.eu/eurostat/databrowser/view/hlth_ehis_bm1e/default/table

All data retrieved from the official Eurostat REST API (JSON:stat format).

## Source Code

GitHub repository: https://github.com/E-l-i-s/eurostat-health-dashboard

## Known Limitations

- EHIS survey data is self-reported, introducing social desirability bias (overreporting of physical activity, underreporting of weight)
- Only two survey waves exist (2014, 2019), limiting time-series analysis (the 2008 EHIS wave used different dataset codes and is not included)
- Small-cell suppression by Eurostat for confidentiality reduces available data for smaller countries and narrow demographic groups
- Cross-country comparability depends on consistent survey administration, which may vary
