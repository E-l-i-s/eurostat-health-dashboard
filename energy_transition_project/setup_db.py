import sqlite3
import pandas as pd
import numpy as np

def setup_energy_db():
    conn = sqlite3.connect("energy_transition_project/energy.db")
    cursor = conn.cursor()

    # Clean start
    cursor.execute("DROP TABLE IF EXISTS Country")
    cursor.execute("DROP TABLE IF EXISTS Year")
    cursor.execute("DROP TABLE IF EXISTS EnergyMetric")
    cursor.execute("DROP TABLE IF EXISTS EnergyValue")
    cursor.execute("DROP TABLE IF EXISTS EnergySource")
    cursor.execute("DROP TABLE IF EXISTS EnergySourceValue")
    cursor.execute("DROP TABLE IF EXISTS Emissions")
    cursor.execute("DROP TABLE IF EXISTS GDP_Data")

    # Create Tables
    cursor.execute("CREATE TABLE Country (CountryID INTEGER PRIMARY KEY, Name TEXT, ISO_Code TEXT)")
    cursor.execute("CREATE TABLE Year (YearID INTEGER PRIMARY KEY, Year INTEGER)")
    cursor.execute("CREATE TABLE EnergyMetric (MetricID INTEGER PRIMARY KEY, MetricName TEXT, Unit TEXT)")
    cursor.execute("CREATE TABLE EnergyValue (ValueID INTEGER PRIMARY KEY, CountryID INTEGER, YearID INTEGER, MetricID INTEGER, Value REAL, FOREIGN KEY(CountryID) REFERENCES Country(CountryID), FOREIGN KEY(YearID) REFERENCES Year(YearID), FOREIGN KEY(MetricID) REFERENCES EnergyMetric(MetricID))")
    cursor.execute("CREATE TABLE EnergySource (SourceID INTEGER PRIMARY KEY, SourceName TEXT)")
    cursor.execute("CREATE TABLE EnergySourceValue (SourceValueID INTEGER PRIMARY KEY, CountryID INTEGER, YearID INTEGER, SourceID INTEGER, Value REAL, FOREIGN KEY(CountryID) REFERENCES Country(CountryID), FOREIGN KEY(YearID) REFERENCES Year(YearID), FOREIGN KEY(SourceID) REFERENCES EnergySource(SourceID))")
    cursor.execute("CREATE TABLE Emissions (EmissionID INTEGER PRIMARY KEY, CountryID INTEGER, YearID INTEGER, CO2_Amount REAL, FOREIGN KEY(CountryID) REFERENCES Country(CountryID), FOREIGN KEY(YearID) REFERENCES Year(YearID))")
    cursor.execute("CREATE TABLE GDP_Data (GDPID INTEGER PRIMARY KEY, CountryID INTEGER, YearID INTEGER, GDP_Value REAL, FOREIGN KEY(CountryID) REFERENCES Country(CountryID), FOREIGN KEY(YearID) REFERENCES Year(YearID))")

    # Load Data
    df = pd.read_csv("energy_transition_project/data/austria_energy_cleaned.csv")

    # 1. Country & Year
    cursor.execute("INSERT INTO Country (Name, ISO_Code) VALUES (?, ?)", ('Austria', 'AUT'))
    country_id = 1

    years = sorted(df['year'].unique())
    for i, y in enumerate(years):
        cursor.execute("INSERT INTO Year (YearID, Year) VALUES (?, ?)", (i+1, int(y)))
    year_map = {int(y): i+1 for i, y in enumerate(years)}

    # 2. Energy Metrics
    metrics = [
        (1, 'Renewables Share (%)', '%'),
        (2, 'Fossil Fuel Share (%)', '%'),
        (3, 'Carbon Intensity', 'kg/kWh')
    ]
    cursor.executemany("INSERT INTO EnergyMetric (MetricID, MetricName, Unit) VALUES (?, ?, ?)", metrics)

    # 3. Energy Sources
    sources = [
        (1, 'Coal'),
        (2, 'Oil'),
        (3, 'Gas'),
        (4, 'Solar'),
        (5, 'Wind'),
        (6, 'Hydro')
    ]
    cursor.executemany("INSERT INTO EnergySource (SourceID, SourceName) VALUES (?, ?)", sources)

    # 4. Populate EnergyValue
    for idx, row in df.iterrows():
        year_id = year_map[int(row['year'])]
        
        # Renewables
        val_r = row['renewables_share_elec']
        if not pd.isna(val_r):
            cursor.execute("INSERT INTO EnergyValue (CountryID, YearID, MetricID, Value) VALUES (?, ?, ?, ?)",
                           (country_id, year_id, 1, float(val_r)))
        
        # Fossil
        val_f = row['fossil_share_elec']
        if not pd.isna(val_f):
            cursor.execute("INSERT INTO EnergyValue (CountryID, YearID, MetricID, Value) VALUES (?, ?, ?, ?)",
                           (country_id, year_id, 2, float(val_f)))

    # 5. Populate EnergySourceValue
    for idx, row in df.iterrows():
        year_id = year_map[int(row['year'])]
        
        mapping = {
            'coal_consumption': 1,
            'oil_consumption': 2,
            'gas_consumption': 3,
            'solar_consumption': 4,
            'wind_consumption': 5,
            'hydro_consumption': 6
        }
        
        for col, src_id in mapping.items():
            if col in df.columns:
                val = row[col]
                if not pd.isna(val):
                    cursor.execute("INSERT INTO EnergySourceValue (CountryID, YearID, SourceID, Value) VALUES (?, ?, ?, ?)",
                                   (country_id, year_id, src_id, float(val)))

    # 6. Populate Emissions & GDP
    for idx, row in df.iterrows():
        year_id = year_map[int(row['year'])]
        
        # CO2
        co2_col = 'co2_emissions' if 'co2_emissions' in df.columns else 'greenhouse_gas_emissions'
        if co2_col in df.columns:
            val_co2 = row[co2_col]
            if not pd.isna(val_co2):
                cursor.execute("INSERT INTO Emissions (CountryID, YearID, CO2_Amount) VALUES (?, ?, ?)",
                               (country_id, year_id, float(val_co2)))
        
        # GDP
        if 'gdp' in df.columns:
            val_gdp = row['gdp']
            if not pd.isna(val_gdp):
                cursor.execute("INSERT INTO GDP_Data (CountryID, YearID, GDP_Value) VALUES (?, ?, ?)",
                               (country_id, year_id, float(val_gdp)))

    conn.commit()
    conn.close()
    print("Energy database setup and population complete.")

if __name__ == "__main__":
    setup_energy_db()
