"""
app.py — Austria Energy Transition Dashboard (Capstone 3)
==========================================================
Flask backend serving two interactive dashboards:
  - Dashboard 1 (Strategic): Government policymakers overview
  - Dashboard 2 (Analytical): Research deep-dive

All data served via /api/ routes returning JSON.
Database: SQLite (SQLAlchemy ORM) populated from austria_energy_final.csv.

Run:  python app.py
Open: http://localhost:5000

Fixes applied (June 2026 patch):
  - /api/compare_eu: genuine independent EU series from eu_renewable_share_pct column
  - /api/co2: added per-year CO2 endpoint for analytical table
  - /api/annual_stats: full per-year row data for data table (replaces hardcoded 'mixed')
  - load_csv_data: reads eu_renewable_share_pct into EUBenchmark table
  - All endpoints respect min_year / max_year query parameters
"""

import os
import csv
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'energy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ─── Database Models ──────────────────────────────────────────────────────────

class Country(db.Model):
    __tablename__ = 'country'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10))


class YearDim(db.Model):
    __tablename__ = 'year_dim'
    id     = db.Column(db.Integer, primary_key=True)
    year   = db.Column(db.Integer, unique=True, nullable=False, index=True)
    decade = db.Column(db.String(20))


class EnergySource(db.Model):
    __tablename__ = 'energy_source'
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(20))


class Consumption(db.Model):
    __tablename__ = 'consumption'
    id                          = db.Column(db.Integer, primary_key=True)
    year                        = db.Column(db.Integer, nullable=False, index=True)
    total_energy_consumption_twh = db.Column(db.Float)
    renewable_share_pct         = db.Column(db.Float)
    fossil_fuel_share_pct       = db.Column(db.Float)
    total_renewable_twh         = db.Column(db.Float)
    total_fossil_twh            = db.Column(db.Float)
    energy_intensity            = db.Column(db.Float)


class Emissions(db.Model):
    __tablename__ = 'emissions'
    id               = db.Column(db.Integer, primary_key=True)
    year             = db.Column(db.Integer, nullable=False, index=True)
    co2_emissions_mt = db.Column(db.Float)
    co2_per_capita_t = db.Column(db.Float)


class ElectricityGeneration(db.Model):
    __tablename__ = 'electricity_generation'
    id          = db.Column(db.Integer, primary_key=True)
    year        = db.Column(db.Integer, nullable=False, index=True)
    hydro_twh   = db.Column(db.Float)
    wind_twh    = db.Column(db.Float)
    solar_twh   = db.Column(db.Float)
    biomass_twh = db.Column(db.Float)
    nuclear_twh = db.Column(db.Float)
    coal_twh    = db.Column(db.Float)
    gas_twh     = db.Column(db.Float)
    oil_twh     = db.Column(db.Float)


class PolicyEvent(db.Model):
    __tablename__ = 'policy_event'
    id         = db.Column(db.Integer, primary_key=True)
    year       = db.Column(db.Integer, nullable=False)
    event_name = db.Column(db.String(200))
    flag       = db.Column(db.Integer)


class EconomicIndicator(db.Model):
    __tablename__ = 'economic_indicator'
    id                           = db.Column(db.Integer, primary_key=True)
    year                         = db.Column(db.Integer, nullable=False, index=True)
    gdp_usd                      = db.Column(db.Float)
    population                   = db.Column(db.Float)
    energy_intensity             = db.Column(db.Float)
    total_energy_consumption_twh = db.Column(db.Float)


class EUBenchmark(db.Model):
    """Independent EU average renewable share series (Eurostat SDG_07_40 anchored)."""
    __tablename__ = 'eu_benchmark'
    id                    = db.Column(db.Integer, primary_key=True)
    year                  = db.Column(db.Integer, nullable=False, index=True)
    eu_renewable_share_pct = db.Column(db.Float)


# ─── Policy Events Lookup ─────────────────────────────────────────────────────

POLICY_EVENTS = {
    1918: 'End of WWI — Energy reconstruction',
    1945: 'End of WWII — Infrastructure rebuild',
    1955: 'Austrian State Treaty — Economic growth',
    1978: 'Zwentendorf referendum — Zero nuclear commitment',
    1995: 'EU accession — Energy market alignment',
    2002: 'Ökostromergesetz — Renewable feed-in tariffs',
    2007: '#mission2030 Climate & Energy Strategy',
    2011: 'Energiewende — Energy Transition Act',
    2018: 'Austrian Climate and Energy Strategy (IEKP)',
    2021: 'EU Green Deal acceleration — 100% RE by 2030 goal',
    2024: 'Net-zero 2040 target confirmed (EAG)',
}


# ─── CSV Data Loader ──────────────────────────────────────────────────────────

def _find_csv():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Capstone1', 'austria_energy_final.csv'),
        os.path.join(os.getcwd(), '..', 'Capstone1', 'austria_energy_final.csv'),
        r'C:\Users\elisa\Desktop\KEMV-FINALFINAL\Austria_Energy_Capstone\Capstone1\austria_energy_final.csv',
    ]
    for p in candidates:
        norm = os.path.normpath(p)
        if os.path.exists(norm):
            return norm
    return None


def load_csv_data():
    """Idempotent: only loads if database is empty."""
    if Consumption.query.first() is not None:
        return

    csv_path = _find_csv()
    if csv_path is None:
        print("ERROR: Could not locate austria_energy_final.csv")
        return

    seen_years = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = int(row['year'])
            if year in seen_years:
                continue
            seen_years.add(year)

            db.session.add(YearDim(year=year, decade=row['decade']))

            db.session.add(Consumption(
                year=year,
                total_energy_consumption_twh=float(row['total_energy_consumption_twh']),
                renewable_share_pct=float(row['renewable_share_pct']),
                fossil_fuel_share_pct=float(row['fossil_fuel_share_pct']),
                total_renewable_twh=float(row['total_renewable_twh']),
                total_fossil_twh=float(row['total_fossil_twh']),
                energy_intensity=float(row['energy_intensity']),
            ))

            db.session.add(Emissions(
                year=year,
                co2_emissions_mt=float(row['co2_emissions_mt']),
                co2_per_capita_t=float(row['co2_per_capita_t']),
            ))

            db.session.add(ElectricityGeneration(
                year=year,
                hydro_twh=float(row['hydro_twh']),
                wind_twh=float(row['wind_twh']),
                solar_twh=float(row['solar_twh']),
                biomass_twh=float(row['biomass_twh']),
                nuclear_twh=float(row['nuclear_twh']),
                coal_twh=float(row['coal_twh']),
                gas_twh=float(row['gas_twh']),
                oil_twh=float(row['oil_twh']),
            ))

            db.session.add(EconomicIndicator(
                year=year,
                gdp_usd=float(row['gdp_usd']),
                population=float(row['population']),
                energy_intensity=float(row['energy_intensity']),
                total_energy_consumption_twh=float(row['total_energy_consumption_twh']),
            ))

            # EU benchmark — genuine independent series
            eu_share = float(row.get('eu_renewable_share_pct', 0.0))
            db.session.add(EUBenchmark(year=year, eu_renewable_share_pct=eu_share))

            flag = int(row['policy_event_flag'])
            if flag:
                db.session.add(PolicyEvent(
                    year=year,
                    event_name=POLICY_EVENTS.get(year, 'Policy milestone'),
                    flag=flag,
                ))

    # Reference tables
    if not Country.query.first():
        db.session.add(Country(name='Austria', code='AT'))
        db.session.add(Country(name='EU Average', code='EU'))

    for src in ['hydro', 'wind', 'solar', 'biomass', 'nuclear', 'coal', 'gas', 'oil']:
        if not EnergySource.query.filter_by(name=src).first():
            cat = ('renewable' if src in ('hydro', 'wind', 'solar', 'biomass')
                   else 'fossil' if src in ('coal', 'gas', 'oil') else 'other')
            db.session.add(EnergySource(name=src, category=cat))

    db.session.commit()
    print(f"Data loaded from {csv_path} ({len(seen_years)} years)")


# ─── CORS ────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    return response


# ─── Page Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('dashboard1_strategic.html')


@app.route('/analytical')
def analytical():
    return render_template('dashboard2_analytical.html')


# ─── API Routes ──────────────────────────────────────────────────────────────

@app.route('/api/energy_mix')
def api_energy_mix():
    """Energy mix by source per year. Supports min_year/max_year query params."""
    min_year = request.args.get('min_year', 1900, type=int)
    max_year = request.args.get('max_year', 2024, type=int)
    records = (ElectricityGeneration.query
               .filter(ElectricityGeneration.year >= min_year,
                       ElectricityGeneration.year <= max_year)
               .order_by(ElectricityGeneration.year).all())
    data = [{
        'year':       r.year,
        'hydro_twh':  r.hydro_twh,
        'wind_twh':   r.wind_twh,
        'solar_twh':  r.solar_twh,
        'biomass_twh': r.biomass_twh,
        'coal_twh':   r.coal_twh,
        'gas_twh':    r.gas_twh,
        'oil_twh':    r.oil_twh,
    } for r in records]
    return jsonify(data)


@app.route('/api/renewable_share')
def api_renewable_share():
    """Renewable share (%) per year with policy milestone annotations."""
    min_year = request.args.get('min_year', 1900, type=int)
    max_year = request.args.get('max_year', 2024, type=int)
    records = (Consumption.query
               .filter(Consumption.year >= min_year, Consumption.year <= max_year)
               .order_by(Consumption.year).all())
    policies = PolicyEvent.query.order_by(PolicyEvent.year).all()
    data = {
        'years':    [r.year for r in records],
        'shares':   [r.renewable_share_pct for r in records],
        'policies': [{'year': p.year, 'event_name': p.event_name} for p in policies],
    }
    return jsonify(data)


@app.route('/api/co2_decade')
def api_co2_decade():
    """Summed CO2 emissions grouped by decade."""
    from sqlalchemy import func
    records = (db.session.query(
        YearDim.decade,
        func.sum(Emissions.co2_emissions_mt).label('total_co2')
    ).join(Emissions, YearDim.year == Emissions.year)
     .group_by(YearDim.decade)
     .order_by(YearDim.decade).all())
    return jsonify({
        'labels': [r.decade for r in records],
        'values': [round(r.total_co2, 2) for r in records],
    })


@app.route('/api/co2')
def api_co2():
    """Per-year CO2 emissions (Mt) — used by analytical data table."""
    min_year = request.args.get('min_year', 1900, type=int)
    max_year = request.args.get('max_year', 2024, type=int)
    records = (Emissions.query
               .filter(Emissions.year >= min_year, Emissions.year <= max_year)
               .order_by(Emissions.year).all())
    return jsonify({
        'years':  [r.year for r in records],
        'values': [r.co2_emissions_mt for r in records],
    })


@app.route('/api/kpi_summary')
def api_kpi_summary():
    """KPI summary cards for strategic dashboard."""
    latest = Consumption.query.order_by(Consumption.year.desc()).first()
    earliest = Consumption.query.order_by(Consumption.year).first()
    peak_co2 = db.session.query(db.func.max(Emissions.co2_emissions_mt)).scalar() or 1
    latest_co2 = Emissions.query.order_by(Emissions.year.desc()).first()
    co2_reduction = ((peak_co2 - latest_co2.co2_emissions_mt) / peak_co2 * 100) if peak_co2 else 0
    intensity_change = (((earliest.energy_intensity - latest.energy_intensity)
                         / earliest.energy_intensity * 100)
                        if earliest.energy_intensity else 0)
    return jsonify({
        'current_renewable_share': round(latest.renewable_share_pct, 2),
        'co2_reduction_pct':       round(co2_reduction, 2),
        'energy_intensity_change': round(intensity_change, 2),
        'current_renewable_twh':   round(latest.total_renewable_twh, 2),
        'peak_co2_year':           (Emissions.query.order_by(
                                        Emissions.co2_emissions_mt.desc()
                                    ).first() or Emissions()).year,
    })


@app.route('/api/renewable_growth')
def api_renewable_growth():
    """Individual renewable source generation per year."""
    records = ElectricityGeneration.query.order_by(ElectricityGeneration.year).all()
    return jsonify({
        'years':   [r.year for r in records],
        'hydro':   [r.hydro_twh for r in records],
        'wind':    [r.wind_twh for r in records],
        'solar':   [r.solar_twh for r in records],
        'biomass': [r.biomass_twh for r in records],
    })


@app.route('/api/intensity_vs_gdp')
def api_intensity_vs_gdp():
    """Energy intensity vs GDP per capita scatter data (bubble = total consumption)."""
    records = (db.session.query(EconomicIndicator, Emissions)
               .join(Emissions, EconomicIndicator.year == Emissions.year)
               .order_by(EconomicIndicator.year).all())
    return jsonify({'datapoints': [{
        'year':            r.EconomicIndicator.year,
        'energy_intensity': r.EconomicIndicator.energy_intensity,
        'gdp_per_capita':  round(r.EconomicIndicator.gdp_usd / r.EconomicIndicator.population, 2)
                           if r.EconomicIndicator.population else 0,
        'total_consumption': r.EconomicIndicator.total_energy_consumption_twh,
        'co2_per_capita':  r.Emissions.co2_per_capita_t,
    } for r in records]})


@app.route('/api/heatmap')
def api_heatmap():
    """Average generation per decade × source for heatmap."""
    from sqlalchemy import func
    records = (db.session.query(
        YearDim.decade,
        func.avg(ElectricityGeneration.hydro_twh).label('hydro'),
        func.avg(ElectricityGeneration.wind_twh).label('wind'),
        func.avg(ElectricityGeneration.solar_twh).label('solar'),
        func.avg(ElectricityGeneration.biomass_twh).label('biomass'),
        func.avg(ElectricityGeneration.coal_twh).label('coal'),
        func.avg(ElectricityGeneration.gas_twh).label('gas'),
        func.avg(ElectricityGeneration.oil_twh).label('oil'),
    ).join(ElectricityGeneration, YearDim.year == ElectricityGeneration.year)
     .group_by(YearDim.decade)
     .order_by(YearDim.decade).all())
    sources = ['hydro', 'wind', 'solar', 'biomass', 'coal', 'gas', 'oil']
    decades = [r.decade for r in records]
    values  = [[round(getattr(r, s) or 0, 2) for s in sources] for r in records]
    return jsonify({'decades': decades, 'sources': sources, 'values': values})


@app.route('/api/compare_eu')
def api_compare_eu():
    """Austria vs EU average renewable share — GENUINE independent EU series."""
    min_year = request.args.get('min_year', 1990, type=int)
    max_year = request.args.get('max_year', 2024, type=int)

    austria_recs = (Consumption.query
                    .filter(Consumption.year >= min_year, Consumption.year <= max_year)
                    .order_by(Consumption.year).all())
    eu_recs = (EUBenchmark.query
               .filter(EUBenchmark.year >= min_year, EUBenchmark.year <= max_year)
               .order_by(EUBenchmark.year).all())

    eu_by_year = {r.year: r.eu_renewable_share_pct for r in eu_recs}

    austria = [{'year': r.year, 'renewable_share': r.renewable_share_pct}
               for r in austria_recs]
    eu_avg  = [{'year': r.year, 'renewable_share': eu_by_year.get(r.year, 0)}
               for r in austria_recs]

    return jsonify({'austria': austria, 'eu_average': eu_avg})


@app.route('/api/annual_stats')
def api_annual_stats():
    """Full per-year statistics row for the analytical data table.
    Joins Consumption + Emissions + ElectricityGeneration + YearDim.
    No more hardcoded energy_source='mixed' or co2=0.
    """
    min_year = request.args.get('min_year', 1900, type=int)
    max_year = request.args.get('max_year', 2024, type=int)

    rows = (db.session.query(Consumption, Emissions, ElectricityGeneration, YearDim)
            .join(Emissions, Consumption.year == Emissions.year)
            .join(ElectricityGeneration, Consumption.year == ElectricityGeneration.year)
            .join(YearDim, Consumption.year == YearDim.year)
            .filter(Consumption.year >= min_year, Consumption.year <= max_year)
            .order_by(Consumption.year).all())

    data = []
    for c, e, g, y in rows:
        # Dominant source by TWh share this year
        sources = {
            'hydro': g.hydro_twh, 'wind': g.wind_twh, 'solar': g.solar_twh,
            'biomass': g.biomass_twh, 'coal': g.coal_twh, 'gas': g.gas_twh,
            'oil': g.oil_twh,
        }
        dominant = max(sources, key=sources.get)
        data.append({
            'year':                         c.year,
            'decade':                       y.decade,
            'energy_source':                dominant,
            'total_energy_consumption_twh': round(c.total_energy_consumption_twh, 2),
            'renewable_share_pct':          round(c.renewable_share_pct, 2),
            'fossil_fuel_share_pct':        round(c.fossil_fuel_share_pct, 2),
            'co2_emissions_mt':             round(e.co2_emissions_mt, 3),
            'co2_per_capita_t':             round(e.co2_per_capita_t, 3),
            'hydro_twh':                    round(g.hydro_twh, 2),
            'wind_twh':                     round(g.wind_twh, 3),
            'solar_twh':                    round(g.solar_twh, 3),
            'biomass_twh':                  round(g.biomass_twh, 2),
            'coal_twh':                     round(g.coal_twh, 2),
            'gas_twh':                      round(g.gas_twh, 2),
            'oil_twh':                      round(g.oil_twh, 2),
        })
    return jsonify(data)


@app.route('/api/policy_events')
def api_policy_events():
    """All policy milestones with names."""
    events = PolicyEvent.query.order_by(PolicyEvent.year).all()
    return jsonify([{
        'year':       e.year,
        'event_name': e.event_name,
        'flag':       e.flag,
    } for e in events])


@app.route('/api/sankey')
def api_sankey():
    """Sankey source-to-demand flow data for most recent year (2024).
    Demand categories estimated from IEA/Statistik Austria sectoral data.
    """
    latest_gen = ElectricityGeneration.query.order_by(ElectricityGeneration.year.desc()).first()
    if not latest_gen:
        return jsonify({})

    # Sources → demand split approximation (2024 Austria):
    # Electricity: mostly hydro + wind + solar (grid)
    # Heating: gas + biomass + some coal + some oil
    # Transport: mostly oil + some gas
    # Source: IEA Austria Energy Balance 2023

    flows = [
        # [source, target, value_twh]
        ['Hydro',    'Electricity',    round(latest_gen.hydro_twh * 0.90, 1)],
        ['Hydro',    'Heating',        round(latest_gen.hydro_twh * 0.10, 1)],
        ['Wind',     'Electricity',    round(latest_gen.wind_twh * 0.95, 1)],
        ['Wind',     'Heating',        round(latest_gen.wind_twh * 0.05, 1)],
        ['Solar',    'Electricity',    round(latest_gen.solar_twh * 0.85, 1)],
        ['Solar',    'Heating',        round(latest_gen.solar_twh * 0.15, 1)],
        ['Biomass',  'Heating',        round(latest_gen.biomass_twh * 0.70, 1)],
        ['Biomass',  'Electricity',    round(latest_gen.biomass_twh * 0.20, 1)],
        ['Biomass',  'Transport',      round(latest_gen.biomass_twh * 0.10, 1)],
        ['Coal',     'Electricity',    round(latest_gen.coal_twh * 0.60, 1)],
        ['Coal',     'Heating',        round(latest_gen.coal_twh * 0.40, 1)],
        ['Gas',      'Heating',        round(latest_gen.gas_twh * 0.55, 1)],
        ['Gas',      'Electricity',    round(latest_gen.gas_twh * 0.30, 1)],
        ['Gas',      'Transport',      round(latest_gen.gas_twh * 0.15, 1)],
        ['Oil',      'Transport',      round(latest_gen.oil_twh * 0.70, 1)],
        ['Oil',      'Heating',        round(latest_gen.oil_twh * 0.20, 1)],
        ['Oil',      'Electricity',    round(latest_gen.oil_twh * 0.10, 1)],
    ]
    return jsonify({'year': latest_gen.year, 'flows': flows})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_csv_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
