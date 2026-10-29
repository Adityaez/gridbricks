"""Integration and contract tests for FastAPI REST endpoints."""
import json
import os
from datetime import date
from unittest.mock import AsyncMock, patch
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def mock_normalized_data():
    """Load real normalized fixtures for January 15, 2026."""
    from app.services.elexon import ElexonClient
    elexon = ElexonClient()

    with open(os.path.join(FIXTURES_DIR, "fuelhh_2026_01_15.json"), "r", encoding="utf-8") as f:
        fuelhh_raw = json.load(f)
    with open(os.path.join(FIXTURES_DIR, "windfor_2026_01_15.json"), "r", encoding="utf-8") as f:
        windfor_raw = json.load(f)

    target_date = date(2026, 1, 15)
    actuals_df = elexon.normalize_fuelhh(fuelhh_raw)
    forecasts_df = elexon.normalize_windfor(windfor_raw, start_date=target_date, end_date=target_date)
    return actuals_df, forecasts_df


def test_health_check():
    """Verify /api/health endpoint returns status ok and version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_dashboard_date_validation():
    """Verify out-of-scope dates return 400 Bad Request."""
    # Date before January 2026
    res_before = client.get("/api/dashboard?date=2025-12-31")
    assert res_before.status_code == 400
    assert "out of bounds" in res_before.json()["detail"].lower()

    # Date after January 2026
    res_after = client.get("/api/dashboard?date=2026-02-01")
    assert res_after.status_code == 400
    assert "out of bounds" in res_after.json()["detail"].lower()


def test_dashboard_endpoint_success(mock_normalized_data):
    """Verify /api/dashboard returns 48 intervals and accurate metrics."""
    actuals_df, forecasts_df = mock_normalized_data

    with patch("app.api.routes.elexon_client.fetch_actual_wind", new=AsyncMock(return_value=actuals_df)), \
         patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):

        response = client.get("/api/dashboard?date=2026-01-15&cutoff_rule=day_ahead_1700")
        assert response.status_code == 200
        data = response.json()

        assert data["delivery_date"] == "2026-01-15"
        assert data["cutoff_rule"] == "day_ahead_1700"
        assert len(data["intervals"]) == 48

        metrics = data["metrics"]
        assert metrics["total_expected"] == 48
        assert metrics["matched_intervals"] == 24
        assert metrics["mae_mw"] is not None and metrics["mae_mw"] > 0
        assert metrics["rmse_mw"] is not None and metrics["rmse_mw"] > 0
        assert metrics["wape_percent"] is not None and metrics["wape_percent"] > 0


def test_dashboard_hourly_expansion(mock_normalized_data):
    """Verify hourly expansion increases matched intervals to 48."""
    actuals_df, forecasts_df = mock_normalized_data

    with patch("app.api.routes.elexon_client.fetch_actual_wind", new=AsyncMock(return_value=actuals_df)), \
         patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):

        response = client.get("/api/dashboard?date=2026-01-15&cutoff_rule=day_ahead_1700&hourly_expansion=true")
        assert response.status_code == 200
        data = response.json()

        assert data["hourly_expansion"] is True
        assert data["metrics"]["matched_intervals"] == 48
        assert data["metrics"]["missing_forecasts"] == 0


def test_analytics_date_validation():
    """Verify /api/analytics rejects invalid date ranges."""
    # from > to
    res_range = client.get("/api/analytics?from=2026-01-15&to=2026-01-10")
    assert res_range.status_code == 400
    assert "on or before" in res_range.json()["detail"].lower()

    # Out of scope
    res_out = client.get("/api/analytics?from=2025-12-30&to=2026-01-05")
    assert res_out.status_code == 400


def test_analytics_endpoint_success(mock_normalized_data):
    """Verify /api/analytics returns multi-day aggregate and breakdown."""
    actuals_df, forecasts_df = mock_normalized_data

    with patch("app.api.routes.elexon_client.fetch_actual_wind", new=AsyncMock(return_value=actuals_df)), \
         patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):

        response = client.get("/api/analytics?from=2026-01-15&to=2026-01-15&cutoff_rule=day_ahead_1700")
        assert response.status_code == 200
        data = response.json()

        assert data["date_from"] == "2026-01-15"
        assert data["date_to"] == "2026-01-15"
        assert len(data["daily_breakdown"]) == 1
        assert data["aggregate_metrics"]["total_expected"] == 48


def test_forecast_evolution_endpoint(mock_normalized_data):
    """Verify /api/forecast-evolution returns chronological revisions and pre/post cutoff tags."""
    _, forecasts_df = mock_normalized_data

    with patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):
        response = client.get("/api/forecast-evolution?date=2026-01-15&interval_start=2026-01-15T12:00:00Z")
        assert response.status_code == 200
        data = response.json()

        assert data["delivery_date"] == "2026-01-15"
        assert "revisions" in data
        assert len(data["revisions"]) > 0

        # Check revision structure
        rev = data["revisions"][0]
        assert "publish_time" in rev
        assert "forecast_mw" in rev
        assert "is_pre_cutoff" in rev


def test_upstream_error_handling():
    """Verify 502 Bad Gateway is returned when upstream Elexon call raises an error."""
    with patch("app.api.routes.elexon_client.fetch_actual_wind", side_effect=RuntimeError("Elexon timeout")):
        response = client.get("/api/dashboard?date=2026-01-15")
        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()
