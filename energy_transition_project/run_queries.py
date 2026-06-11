import sqlite3
import pandas as pd

def run_queries():
    conn = sqlite3.connect("energy_transition_project/energy.db")
    
    queries = {
        "Easy 1: Available Energy Sources": "SELECT SourceName FROM EnergySource",
        "Easy 2: Latest Renewable Share (%)": "SELECT Value FROM EnergyValue WHERE MetricID = 1 ORDER BY YearID DESC LIMIT 1",
        "Medium 1: Fossil Fuel Share Trend (Since 1990)": "SELECT Year, Value FROM EnergyValue JOIN Year ON EnergyValue.YearID = Year.YearID WHERE MetricID = 2 AND Year >= 1990 ORDER BY Year ASC",
        "Medium 2: Top 5 Years for Wind Production": """
            SELECT y.Year, esv.Value as Wind_Cons 
            FROM EnergySourceValue esv 
            JOIN EnergySource es ON esv.SourceID = es.SourceID 
            JOIN Year y ON esv.YearID = y.YearID 
            WHERE es.SourceName = 'Wind' AND esv.Value > 0 
            ORDER BY esv.Value DESC 
            LIMIT 5
        """,
        "Difficult 1: Renewable to Fossil Ratio (Since 1990)": """
            SELECT y.Year, 
                   ROUND(rev.Value / fos.Value, 2) as Ratio
            FROM EnergyValue rev
            JOIN EnergyValue fos ON rev.YearID = fos.YearID AND rev.CountryID = fos.CountryID
            JOIN Year y ON rev.YearID = y.YearID
            WHERE rev.MetricID = 1 AND fos.MetricID = 2 AND fos.Value > 0 AND y.Year >= 1990
            ORDER BY y.Year ASC
        """
    }
    
    results = {}
    for name, query in queries.items():
        results[name] = pd.read_sql_query(query, conn)
        
    conn.close()
    return results

if __name__ == "__main__":
    res = run_queries()
    for name, df in res.items():
        print(f"--- {name} ---")
        print(df.head())
        print("\n")
