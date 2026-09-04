import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

init_db()
client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "WeatherGPT"


def test_weather_forecast_endpoint():
    response = client.get("/api/v1/weather/forecast?latitude=17.3850&longitude=78.4867&days=3")
    assert response.status_code == 200
    data = response.json()
    assert "current" in data
    assert "hourly" in data
    assert "daily" in data
    assert "trust" in data


def test_active_alerts_endpoint():
    response = client.get("/api/v1/alerts/active?latitude=17.3850&longitude=78.4867")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "highest_severity" in data


def test_location_search_endpoint():
    response = client.get("/api/v1/locations/search?q=Hyderabad")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    assert data["results"][0]["name"] == "Hyderabad"


def test_admin_metrics_endpoint():
    response = client.get("/api/v1/admin/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "system_status" in data
    assert "sources_health" in data
