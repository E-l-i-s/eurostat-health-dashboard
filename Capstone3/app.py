import sqlite3
from pathlib import Path
from flask import Flask, g, jsonify, render_template, request

DB_PATH = Path(__file__).parent.parent / "Capstone2" / "capstone.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def value_expr():
    return "CASE WHEN hi.category_code = 'physical_activity' THEN 100 - m.value ELSE m.value END"


def create_app():
    app = Flask(__name__)
    app.teardown_appcontext(close_db)

    @app.route("/")
    def dashboard1():
        return render_template("index.html")

    @app.route("/analytics")
    def dashboard2():
        return render_template("dashboard2.html")

    @app.route("/api/countries")
    def api_countries():
        try:
            db = get_db()
            rows = db.execute(
                "SELECT country_code, country_name FROM Country ORDER BY country_name"
            ).fetchall()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/indicators")
    def api_indicators():
        try:
            db = get_db()
            rows = db.execute("""
                SELECT hi.indicator_code, hi.indicator_label, ic.category_name
                FROM HealthIndicator hi
                JOIN IndicatorCategory ic ON hi.category_code = ic.category_code
                ORDER BY ic.category_name, hi.indicator_label
            """).fetchall()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/waves")
    def api_waves():
        try:
            db = get_db()
            rows = db.execute(
                "SELECT wave_id, year, description FROM SurveyWave ORDER BY year"
            ).fetchall()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/map-data")
    def api_map_data():
        try:
            indicator = request.args.get("indicator", "")
            wave = request.args.get("wave", "")
            sex = request.args.get("sex", "T")
            if not indicator or not wave:
                return jsonify({"error": "Missing indicator or wave parameter", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT m.country_code, c.country_name,
                       ROUND(AVG({value_expr()}), 1) AS value
                FROM Measurement m
                JOIN Country c ON m.country_code = c.country_code
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                WHERE hi.indicator_code = ?
                  AND m.wave_id = ?
                  AND m.sex_code = ?
                  AND m.age_code = 'TOTAL'
                  AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
                GROUP BY m.country_code
                ORDER BY c.country_name
            """, (indicator, int(wave), sex)).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except ValueError:
            return jsonify({"error": "Invalid wave parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/kpi")
    def api_kpi():
        try:
            wave = request.args.get("wave", "")
            if not wave:
                return jsonify({"error": "Missing wave parameter", "status": 400}), 400
            db = get_db()
            wave_id = int(wave)

            avg_inactivity = db.execute(f"""
                SELECT ROUND(AVG({value_expr()}), 1) AS val
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                JOIN Country c ON m.country_code = c.country_code
                WHERE hi.category_code = 'physical_activity'
                  AND m.wave_id = ? AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
            """, (wave_id,)).fetchone()

            avg_chronic = db.execute(f"""
                SELECT ROUND(AVG({value_expr()}), 1) AS val
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                JOIN Country c ON m.country_code = c.country_code
                WHERE hi.category_code = 'chronic_disease'
                  AND m.wave_id = ? AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
            """, (wave_id,)).fetchone()

            high_burden = db.execute(f"""
                SELECT COUNT(*) AS cnt FROM (
                    SELECT m.country_code
                    FROM Measurement m
                    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                    JOIN Country c ON m.country_code = c.country_code
                    WHERE m.wave_id = ? AND m.sex_code = 'T'
                      AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                      AND c.country_code NOT LIKE 'EU%'
                    GROUP BY m.country_code
                    HAVING
                        MAX(CASE WHEN hi.category_code = 'physical_activity' THEN {value_expr()} END) > 45
                        AND MAX(CASE WHEN hi.category_code = 'chronic_disease' THEN {value_expr()} END) > 30
                )
            """, (wave_id,)).fetchone()

            most_improved = db.execute(f"""
                SELECT c.country_name, ROUND(improvement, 1) AS improvement FROM (
                    SELECT curr.country_code,
                           (prev.avg_val - curr.avg_val) AS improvement
                    FROM (
                        SELECT m.country_code, AVG({value_expr()}) AS avg_val
                        FROM Measurement m
                        JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                        WHERE hi.category_code = 'physical_activity'
                          AND m.wave_id = ? AND m.sex_code = 'T'
                          AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                        GROUP BY m.country_code
                    ) curr
                    JOIN (
                        SELECT m.country_code, AVG({value_expr()}) AS avg_val
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
                "avg_inactivity": avg_inactivity["val"] if avg_inactivity and avg_inactivity["val"] is not None else None,
                "avg_chronic_prevalence": avg_chronic["val"] if avg_chronic and avg_chronic["val"] is not None else None,
                "high_burden_countries": high_burden["cnt"] if high_burden else 0,
                "most_improved_country": most_improved["country_name"] if most_improved else None,
                "improvement": most_improved["improvement"] if most_improved and most_improved["improvement"] else None
            })
        except ValueError:
            return jsonify({"error": "Invalid wave parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/top-countries")
    def api_top_countries():
        try:
            indicator = request.args.get("indicator", "")
            wave = request.args.get("wave", "")
            n = request.args.get("n", 10)
            if not indicator or not wave:
                return jsonify({"error": "Missing indicator or wave parameter", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT c.country_name,
                       ROUND(AVG({value_expr()}), 1) AS value
                FROM Measurement m
                JOIN Country c ON m.country_code = c.country_code
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                WHERE hi.indicator_code = ?
                  AND m.wave_id = ? AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
                GROUP BY m.country_code
                ORDER BY value DESC
                LIMIT ?
            """, (indicator, int(wave), int(n))).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except ValueError:
            return jsonify({"error": "Invalid parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/trend")
    def api_trend():
        try:
            indicator = request.args.get("indicator", "")
            sex = request.args.get("sex", "T")
            if not indicator:
                return jsonify({"error": "Missing indicator parameter", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT sw.year,
                       ROUND(AVG({value_expr()}), 1) AS avg_value
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                JOIN SurveyWave sw ON m.wave_id = sw.wave_id
                JOIN Country c ON m.country_code = c.country_code
                WHERE hi.indicator_code = ?
                  AND m.sex_code = ? AND m.age_code = 'TOTAL'
                  AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
                GROUP BY sw.year
                ORDER BY sw.year
            """, (indicator, sex)).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/scatter")
    def api_scatter():
        try:
            activity = request.args.get("activity", "")
            condition = request.args.get("condition", "")
            wave = request.args.get("wave", "")
            sex = request.args.get("sex", "T")
            if not activity or not condition or not wave:
                return jsonify({"error": "Missing parameters", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT c.country_name,
                       ROUND(act.value, 1) AS inactivity_rate,
                       ROUND(cond.value, 1) AS chronic_prevalence
                FROM (
                    SELECT m.country_code, AVG({value_expr()}) AS value
                    FROM Measurement m
                    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                    WHERE hi.indicator_code = ?
                      AND m.wave_id = ? AND m.sex_code = ?
                      AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                    GROUP BY m.country_code
                ) act
                JOIN (
                    SELECT m.country_code, AVG({value_expr()}) AS value
                    FROM Measurement m
                    JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                    WHERE hi.indicator_code = ?
                      AND m.wave_id = ? AND m.sex_code = ?
                      AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                    GROUP BY m.country_code
                ) cond ON act.country_code = cond.country_code
                JOIN Country c ON act.country_code = c.country_code
                WHERE c.country_code NOT LIKE 'EU%'
                ORDER BY c.country_name
            """, (activity, int(wave), sex, condition, int(wave), sex)).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except ValueError:
            return jsonify({"error": "Invalid wave parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/age-breakdown")
    def api_age_breakdown():
        try:
            country = request.args.get("country", "")
            indicator = request.args.get("indicator", "")
            wave = request.args.get("wave", "")
            if not country or not indicator or not wave:
                return jsonify({"error": "Missing parameters", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT ag.label AS age_group, ag.age_code AS age_code,
                       s.label AS sex,
                       ROUND(AVG({value_expr()}), 1) AS value
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
        except ValueError:
            return jsonify({"error": "Invalid wave parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/histogram")
    def api_histogram():
        try:
            indicator = request.args.get("indicator", "")
            wave = request.args.get("wave", "")
            if not indicator or not wave:
                return jsonify({"error": "Missing parameters", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT ROUND({value_expr()}, 0) AS value_bucket,
                       COUNT(*) AS frequency
                FROM Measurement m
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                JOIN Country c ON m.country_code = c.country_code
                WHERE hi.indicator_code = ?
                  AND m.wave_id = ? AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
                GROUP BY value_bucket
                ORDER BY value_bucket
            """, (indicator, int(wave))).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except ValueError:
            return jsonify({"error": "Invalid wave parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/heatmap")
    def api_heatmap():
        try:
            wave = request.args.get("wave", "")
            if not wave:
                return jsonify({"error": "Missing wave parameter", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT c.country_name, hi.indicator_label,
                       ROUND(AVG({value_expr()}), 1) AS value
                FROM Measurement m
                JOIN Country c ON m.country_code = c.country_code
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                WHERE hi.category_code = 'chronic_disease'
                  AND m.wave_id = ? AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL' AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
                GROUP BY c.country_code, hi.indicator_code
                ORDER BY c.country_name, hi.indicator_label
            """, (int(wave),)).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except ValueError:
            return jsonify({"error": "Invalid wave parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    @app.route("/api/insights")
    def api_insights():
        try:
            indicator = request.args.get("indicator", "")
            wave = request.args.get("wave", "")
            if not indicator or not wave:
                return jsonify({"error": "Missing parameters", "status": 400}), 400
            db = get_db()
            rows = db.execute(f"""
                SELECT 
                    UPPER(c.country_name) || ' (' || COALESCE(c.region, 'Unknown') || ')' AS country_info,
                    hi.indicator_label,
                    ROUND(AVG({value_expr()}), 2) AS average_value,
                    hi.category_code,
                    DATE('now') AS report_date
                FROM Measurement m
                JOIN Country c ON m.country_code = c.country_code
                JOIN HealthIndicator hi ON m.indicator_code = hi.indicator_code
                JOIN SurveyWave sw ON m.wave_id = sw.wave_id
                WHERE hi.indicator_code = ?
                  AND sw.year = ?
                  AND m.sex_code = 'T'
                  AND m.age_code = 'TOTAL'
                  AND m.data_suppressed = 0
                  AND c.country_code NOT LIKE 'EU%'
                GROUP BY c.country_name, c.region, hi.indicator_label, hi.category_code
                HAVING AVG({value_expr()}) > 20
                ORDER BY average_value DESC
                LIMIT 5
            """, (indicator, int(wave))).fetchall()
            if not rows:
                return jsonify({"error": "No data found", "status": 404}), 404
            return jsonify([dict(r) for r in rows])
        except ValueError:
            return jsonify({"error": "Invalid parameter", "status": 400}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": 500}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
