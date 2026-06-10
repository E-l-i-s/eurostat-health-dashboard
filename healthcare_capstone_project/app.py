from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd

app = Flask(__name__)
DB_PATH = "healthcare_capstone_project/energy.db"

def query_db(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard/strategic')
def strategic():
    return render_template('strategic.html')

@app.route('/dashboard/analytical')
def analytical():
    return render_template('analytical.html')

@app.route('/api/strategic-data')
def strategic_data():
    data = {
        "total_records": int(query_db("SELECT COUNT(*) FROM EnergyValue").iloc[0,0]),
        "avg_renewable_share": round(query_db("SELECT AVG(Value) FROM EnergyValue WHERE MetricID = 1 AND YearID >= 100").iloc[0,0], 1) if not query_db("SELECT AVG(Value) FROM EnergyValue WHERE MetricID = 1 AND YearID >= 100").empty else 0,
        "avg_mix_by_type": query_db("SELECT 'Renewables' as Type, AVG(Value) as val FROM EnergyValue WHERE MetricID = 1 AND YearID >= 100 UNION SELECT 'Fossil' as Type, AVG(Value) as val FROM EnergyValue WHERE MetricID = 2 AND YearID >= 100").to_dict(orient='records'),
        "volume_by_source": query_db("SELECT s.SourceName as Name, SUM(ev.Value) as count FROM EnergySourceValue ev JOIN EnergySource s ON ev.SourceID = s.SourceID WHERE ev.YearID >= 100 GROUP BY s.SourceName").to_dict(orient='records'),
        "trend_renewables": query_db("SELECT y.Year, ev.Value FROM EnergyValue ev JOIN Year y ON ev.YearID = y.YearID WHERE ev.MetricID = 1 AND y.Year >= 1990 ORDER BY y.Year ASC").to_dict(orient='records'),
        "trend_fossil": query_db("SELECT y.Year, ev.Value FROM EnergyValue ev JOIN Year y ON ev.YearID = y.YearID WHERE ev.MetricID = 2 AND y.Year >= 1990 ORDER BY y.Year ASC").to_dict(orient='records')
    }
    return jsonify(data)

@app.route('/api/analytical-data')
def analytical_data():
    # Correlation: Renewables vs Fossil
    correlation_data = query_db("""
        SELECT y.Year, rev.Value as Renewables, fos.Value as Fossil
        FROM EnergyValue rev
        JOIN EnergyValue fos ON rev.YearID = fos.YearID AND rev.CountryID = fos.CountryID
        JOIN Year y ON rev.YearID = y.YearID
        WHERE rev.MetricID = 1 AND fos.MetricID = 2 AND y.Year >= 1990
    """)
    
    # Wind vs Coal
    source_data = query_db("""
        SELECT y.Year, w.Value as Wind, c.Value as Coal
        FROM EnergySourceValue w
        JOIN EnergySourceValue c ON w.YearID = c.YearID AND w.CountryID = c.CountryID
        JOIN EnergySource s_w ON w.SourceID = s_w.SourceID
        JOIN EnergySource s_c ON c.SourceID = s_c.SourceID
        JOIN Year y ON w.YearID = y.YearID
        WHERE s_w.SourceName = 'Wind' AND s_c.SourceName = 'Coal' AND y.Year >= 1990
    """)

    data = {
        "renewables_vs_fossil": correlation_data.to_dict(orient='records'),
        "wind_vs_coal": source_data.to_dict(orient='records')
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
