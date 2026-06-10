"""
Flask Application — Capstone 3
Physical Activity and Chronic Disease Burden Across Europe
Two dashboards: Strategic (executive) and Analytical (tactical)
"""

import sqlite3
from pathlib import Path
from flask import Flask, g, jsonify, render_template, request


DB_PATH = Path(__file__).parent.parent / "Capstone2" / "capstone.db"


def get_db():
    """Return a database connection scoped to the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def create_app():
    """Application factory pattern."""
    app = Flask(__name__)
    app.teardown_appcontext(close_db)

    @app.route("/")
    def dashboard1():
        """Render Strategic Dashboard."""
        return render_template("index.html")

    @app.route("/analytics")
    def dashboard2():
        """Render Analytical Dashboard."""
        return render_template("dashboard2.html")

    @app.route("/api/countries")
    def api_countries():
        """Return list of all country codes and names."""
        db = get_db()
        rows = db.execute(
            "SELECT country_code, country_name FROM Country ORDER BY country_name"
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/indicators")
    def api_indicators():
        """Return list of all indicator codes, labels, and categories."""
        db = get_db()
        rows = db.execute("""
            SELECT hi.indicator_code, hi.indicator_label, ic.category_name
            FROM HealthIndicator hi
            JOIN IndicatorCategory ic ON hi.category_code = ic.category_code
            ORDER BY ic.category_name, hi.indicator_label
        """).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/waves")
    def api_waves():
        """Return list of available survey wave years."""
        db = get_db()
        rows = db.execute(
            "SELECT wave_id, year, description FROM SurveyWave ORDER BY year"
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/map-data")
    def api_map_data():
        """Return country code + value for choropleth rendering."""
        indicator = request.args.get("indicator", "")
        wave = request.args.get("wave", "")
        sex = request.args.get("sex", "T")
        if not indicator or not wave:
            return jsonify({"error": "Missing indicator or wave parameter", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT m.country_code, c.country_name, ROUND(AVG(m.value), 1) AS value
            FROM Measurement m
            JOIN Country c ON m.country_code = c.country_code
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE hi.indicator_code = ?
              AND m.wave_id = ?
              AND m.sex_code = ?
              AND m.age_code = 'TOTAL'
              AND m.data_suppressed = 0
            GROUP BY m.country_code
            ORDER BY c.country_name
        """, (indicator, int(wave), sex)).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    @app.route("/api/kpi")
    def api_kpi():
        """Return 4 KPI values for the given wave year."""
        wave = request.args.get("wave", "")
        if not wave:
            return jsonify({"error": "Missing wave parameter", "status": 400}), 400
        db = get_db()
        wave_id = int(wave)

        avg_inactivity = db.execute("""
            SELECT ROUND(AVG(m.value), 1) AS val
            FROM Measurement m
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE hi.category_code = 'physical_activity'
              AND m.wave_id = ? AND m.sex_code = 'T'
              AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
        """, (wave_id,)).fetchone()

        avg_chronic = db.execute("""
            SELECT ROUND(AVG(m.value), 1) AS val
            FROM Measurement m
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE hi.category_code = 'chronic_disease'
              AND m.wave_id = ? AND m.sex_code = 'T'
              AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
        """, (wave_id,)).fetchone()

        high_burden = db.execute("""
            SELECT COUNT(*) AS cnt FROM (
                SELECT m.country_code
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                WHERE m.wave_id = ? AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                GROUP BY m.country_code
                HAVING
                    MAX(CASE WHEN hi.category_code = 'physical_activity' THEN m.value END) > 45
                    AND MAX(CASE WHEN hi.category_code = 'chronic_disease' THEN m.value END) > 30
            )
        """, (wave_id,)).fetchone()

        most_improved = db.execute("""
            SELECT c.country_name, ROUND(improvement, 1) AS improvement FROM (
                SELECT curr.country_code,
                       (prev.avg_val - curr.avg_val) AS improvement
                FROM (
                    SELECT m.country_code, AVG(m.value) AS avg_val
                    FROM Measurement m
                    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                    WHERE hi.category_code = 'physical_activity'
                      AND m.wave_id = ? AND m.sex_code = 'T'
                      AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                    GROUP BY m.country_code
                ) curr
                JOIN (
                    SELECT m.country_code, AVG(m.value) AS avg_val
                    FROM Measurement m
                    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                    WHERE hi.category_code = 'physical_activity'
                      AND m.wave_id = (SELECT MAX(wave_id) FROM SurveyWave WHERE wave_id < ?)
                      AND m.sex_code = 'T' AND m.age_code = 'TOTAL'
                      AND m.data_suppressed = 0
                    GROUP BY m.country_code
                ) prev ON curr.country_code = prev.country_code
                WHERE (prev.avg_val - curr.avg_val) > 0
                ORDER BY improvement DESC
                LIMIT 1
            ) sub
            JOIN Country c ON sub.country_code = c.country_code
        """, (wave_id, wave_id)).fetchone()

        return jsonify({
            "avg_inactivity": avg_inactivity["val"] if avg_inactivity and avg_inactivity["val"] else None,
            "avg_chronic_prevalence": avg_chronic["val"] if avg_chronic and avg_chronic["val"] else None,
            "high_burden_countries": high_burden["cnt"] if high_burden else 0,
            "most_improved_country": most_improved["country_name"] if most_improved else None,
            "improvement": most_improved["improvement"] if most_improved else None
        })

    @app.route("/api/top-countries")
    def api_top_countries():
        """Return top N countries by indicator value."""
        indicator = request.args.get("indicator", "")
        wave = request.args.get("wave", "")
        n = request.args.get("n", 10)
        if not indicator or not wave:
            return jsonify({"error": "Missing indicator or wave parameter", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT c.country_name, ROUND(AVG(m.value), 1) AS value
            FROM Measurement m
            JOIN Country c ON m.country_code = c.country_code
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE hi.indicator_code = ?
              AND m.wave_id = ? AND m.sex_code = 'T'
              AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
            GROUP BY m.country_code
            ORDER BY value DESC
            LIMIT ?
        """, (indicator, int(wave), int(n))).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    @app.route("/api/trend")
    def api_trend():
        """Return EU average value per survey wave."""
        indicator = request.args.get("indicator", "")
        sex = request.args.get("sex", "T")
        if not indicator:
            return jsonify({"error": "Missing indicator parameter", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT sw.year, ROUND(AVG(m.value), 1) AS avg_value
            FROM Measurement m
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            JOIN SurveyWave sw ON m.wave_id = sw.wave_id
            WHERE hi.indicator_code = ?
              AND m.sex_code = ? AND m.age_code = 'TOTAL'
              AND m.data_suppressed = 0
            GROUP BY sw.year
            ORDER BY sw.year
        """, (indicator, sex)).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    @app.route("/api/scatter")
    def api_scatter():
        """Return paired inactivity + prevalence values per country."""
        activity = request.args.get("activity", "")
        condition = request.args.get("condition", "")
        wave = request.args.get("wave", "")
        sex = request.args.get("sex", "T")
        if not activity or not condition or not wave:
            return jsonify({"error": "Missing parameters", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT c.country_name,
                   ROUND(act.value, 1) AS inactivity_rate,
                   ROUND(cond.value, 1) AS chronic_prevalence
            FROM (
                SELECT m.country_code, AVG(m.value) AS value
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                WHERE hi.indicator_code = ?
                  AND m.wave_id = ? AND m.sex_code = ?
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                GROUP BY m.country_code
            ) act
            JOIN (
                SELECT m.country_code, AVG(m.value) AS value
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                WHERE hi.indicator_code = ?
                  AND m.wave_id = ? AND m.sex_code = ?
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                GROUP BY m.country_code
            ) cond ON act.country_code = cond.country_code
            JOIN Country c ON act.country_code = c.country_code
            ORDER BY c.country_name
        """, (activity, int(wave), sex, condition, int(wave), sex)).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    @app.route("/api/age-breakdown")
    def api_age_breakdown():
        """Return values by age group and sex for grouped bar chart."""
        country = request.args.get("country", "")
        indicator = request.args.get("indicator", "")
        wave = request.args.get("wave", "")
        if not country or not indicator or not wave:
            return jsonify({"error": "Missing parameters", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT ag.label AS age_group, ag.age_code AS age_code,
                   s.label AS sex, ROUND(AVG(m.value), 1) AS value
            FROM Measurement m
            JOIN AgeGroup ag ON m.age_code = ag.age_code
            JOIN Sex s ON m.sex_code = s.sex_code
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE m.country_code = ?
              AND hi.indicator_code = ?
              AND m.wave_id = ?
              AND m.data_suppressed = 0
              AND m.age_code != 'TOTAL'
            GROUP BY ag.age_code, s.sex_code
            ORDER BY ag.age_code, s.sex_code
        """, (country, indicator, int(wave))).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    @app.route("/api/histogram")
    def api_histogram():
        """Return value distribution for a selected indicator and wave."""
        indicator = request.args.get("indicator", "")
        wave = request.args.get("wave", "")
        if not indicator or not wave:
            return jsonify({"error": "Missing parameters", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT ROUND(m.value, 0) AS value_bucket, COUNT(*) AS frequency
            FROM Measurement m
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE hi.indicator_code = ?
              AND m.wave_id = ? AND m.sex_code = 'T'
              AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
            GROUP BY value_bucket
            ORDER BY value_bucket
        """, (indicator, int(wave))).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    @app.route("/api/heatmap")
    def api_heatmap():
        """Return country x condition matrix with values."""
        wave = request.args.get("wave", "")
        if not wave:
            return jsonify({"error": "Missing wave parameter", "status": 400}), 400
        db = get_db()
        rows = db.execute("""
            SELECT c.country_name, hi.indicator_label,
                   ROUND(AVG(m.value), 1) AS value
            FROM Measurement m
            JOIN Country c ON m.country_code = c.country_code
            JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
            WHERE hi.category_code = 'chronic_disease'
              AND m.wave_id = ? AND m.sex_code = 'T'
              AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
            GROUP BY c.country_code, hi.indicator_code
            ORDER BY c.country_name, hi.indicator_label
        """, (int(wave),)).fetchall()
        if not rows:
            return jsonify({"error": "No data found", "status": 404}), 404
        return jsonify([dict(r) for r in rows])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
