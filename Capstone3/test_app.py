import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_analytics_route(client):
    response = client.get('/analytics')
    assert response.status_code == 200

def test_api_countries(client):
    response = client.get('/api/countries')
    assert response.status_code == 200

def test_api_indicators(client):
    response = client.get('/api/indicators')
    assert response.status_code == 200

def test_api_waves(client):
    response = client.get('/api/waves')
    assert response.status_code == 200

def test_api_map_data_missing_params(client):
    response = client.get('/api/map-data')
    assert response.status_code == 400

def test_api_map_data_valid(client):
    response = client.get('/api/map-data?indicator=MV_AERO_SPRT&wave=2019')
    assert response.status_code == 200

def test_api_insights_missing_params(client):
    response = client.get('/api/insights')
    assert response.status_code == 400

def test_api_kpi_valid(client):
    response = client.get('/api/kpi?wave=2019')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'avg_inactivity' in data

def test_api_scatter_missing_params(client):
    response = client.get('/api/scatter')
    assert response.status_code == 400

def test_api_heatmap_missing_params(client):
    response = client.get('/api/heatmap')
    assert response.status_code == 400

def test_api_age_breakdown_missing_params(client):
    response = client.get('/api/age-breakdown')
    assert response.status_code == 400
