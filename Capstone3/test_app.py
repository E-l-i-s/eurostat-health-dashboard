import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

def test_index(app):
    client = app.test_client()
    rv = client.get('/')
    assert rv.status_code == 200

def test_analytics(app):
    client = app.test_client()
    rv = client.get('/analytics')
    assert rv.status_code == 200

def test_api_countries(app):
    client = app.test_client()
    rv = client.get('/api/countries')
    assert rv.status_code == 200

def test_api_indicators(app):
    client = app.test_client()
    rv = client.get('/api/indicators')
    assert rv.status_code == 200

def test_api_waves(app):
    client = app.test_client()
    rv = client.get('/api/waves')
    assert rv.status_code == 200

def test_api_map_missing_params(app):
    client = app.test_client()
    rv = client.get('/api/map-data')
    assert rv.status_code == 400

def test_api_map_valid(app):
    client = app.test_client()
    rv = client.get('/api/map-data?indicator=MV_AERO_SPRT&wave=2019')
    assert rv.status_code == 200

def test_api_insights_missing_params(app):
    client = app.test_client()
    rv = client.get('/api/insights')
    assert rv.status_code == 400

def test_api_kpi_valid(app):
    client = app.test_client()
    rv = client.get('/api/kpi?wave=2019')
    assert rv.status_code == 200
    assert 'avg_inactivity' in rv.json

def test_api_scatter_missing_params(app):
    client = app.test_client()
    rv = client.get('/api/scatter')
    assert rv.status_code == 400

def test_api_heatmap_missing_params(app):
    client = app.test_client()
    rv = client.get('/api/heatmap')
    assert rv.status_code == 400

def test_api_age_breakdown_missing_params(app):
    client = app.test_client()
    rv = client.get('/api/age-breakdown')
    assert rv.status_code == 400
