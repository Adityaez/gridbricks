"""End-to-End Integration and User Journey Test Suite for WindSight."""
import json
import os
from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def mock_elexon_fixtures():
    """Load real January 15, 2026 Elexon fixtures for end-to-end flow."""
    from app.services.elexon import ElexonClient
    elexon = ElexonClient()

    with open(os.path.join(FIXTURES_DIR, "fuelhh_2026_01_15.json"), "r", encoding="utf-8") as f:
        fuelhh_raw = json.load(f)
    with open(os.path.join(FIXTURES_DIR, "windfor_2026_01_15.json"), "r", encoding="utf-8") as f:
        windfor_raw = json.load(f)

    actuals_df = elexon.normalize_fuelhh(fuelhh_raw)
    target_date = date(2026, 1, 15)
    forecasts_df = elexon.normalize_windfor(windfor_raw, start_date=target_date, end_date=target_date)
    return actuals_df, forecasts_df


def test_e2e_journey_health_and_root():
    """User Journey 1: Verify service discovery and health check endpoints."""
    # Root discovery
    root_res = client.get("/")
    assert root_res.status_code == 200
    root_data = root_res.json()
    assert "WindSight API is operational" in root_data["message"]
    assert "2026-01-01 to 2026-01-31" in root_data["scope"]

    # Health check
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "ok"
    assert health_data["version"] == "1.0.0"


def test_e2e_journey_daily_dashboard_procurement(mock_elexon_fixtures):
    """
    User Journey 2: Day-Ahead Procurement Desk Workflow.
    Trader inspects wind forecast accuracy for January 15, 2026 using Day-Ahead 17:00 UTC cutoff.
    """
    actuals_df, forecasts_df = mock_elexon_fixtures

    with patch("app.api.routes.elexon_client.fetch_actual_wind", new=AsyncMock(return_value=actuals_df)), \
         patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):

        res = client.get("/api/dashboard?date=2026-01-15&cutoff_rule=day_ahead_1700")
        assert res.status_code == 200
        data = res.json()

        # Verify metadata
        assert data["delivery_date"] == "2026-01-15"
        assert data["cutoff_rule"] == "day_ahead_1700"
        assert data["hourly_expansion"] is False

        # Verify 48 settlement periods are represented
        intervals = data["intervals"]
        assert len(intervals) == 48

        # Verify all settlement periods 1..48 are in chronological sequence
        for idx, item in enumerate(intervals, start=1):
            assert item["settlement_period"] == idx
            assert item["status"] in ("MATCHED", "MISSING_FORECAST", "MISSING_ACTUAL")

        # Verify Look-Ahead Bias Mitigation:
        # Every matched forecast must have publish_time <= 2026-01-14T17:00:00Z
        cutoff_limit = "2026-01-14T17:00:00"
        matched_items = [it for it in intervals if it["status"] == "MATCHED"]
        for it in matched_items:
            assert it["publish_time"] is not None
            assert it["publish_time"] <= cutoff_limit, f"Look-ahead violation: {it['publish_time']} > {cutoff_limit}"
            assert it["forecast_mw"] is not None and it["forecast_mw"] >= 0
            assert it["actual_mw"] is not None and it["actual_mw"] >= 0
            assert round(it["forecast_mw"] - it["actual_mw"], 2) == round(it["error_mw"], 2)

        # Verify summary KPIs
        metrics = data["metrics"]
        assert metrics["total_expected"] == 48
        assert metrics["matched_intervals"] == 24  # 24 on-the-hour intervals
        assert metrics["missing_forecasts"] == 24
        assert metrics["mae_mw"] > 0
        assert metrics["rmse_mw"] > 0
        assert metrics["wape_percent"] > 0


def test_e2e_journey_hourly_expansion(mock_elexon_fixtures):
    """
    User Journey 3: Procurement analyst enables hourly forecast expansion
    to map 60-min WINDFOR forecasts across both half-hours of each delivery hour.
    """
    actuals_df, forecasts_df = mock_elexon_fixtures

    with patch("app.api.routes.elexon_client.fetch_actual_wind", new=AsyncMock(return_value=actuals_df)), \
         patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):

        res = client.get("/api/dashboard?date=2026-01-15&cutoff_rule=day_ahead_1700&hourly_expansion=true")
        assert res.status_code == 200
        data = res.json()

        assert data["hourly_expansion"] is True
        assert data["metrics"]["matched_intervals"] == 48
        assert data["metrics"]["missing_forecasts"] == 0


def test_e2e_journey_range_analytics(mock_elexon_fixtures):
    """
    User Journey 4: Management review of multi-day aggregate forecast bias and MAE.
    """
    actuals_df, forecasts_df = mock_elexon_fixtures

    with patch("app.api.routes.elexon_client.fetch_actual_wind", new=AsyncMock(return_value=actuals_df)), \
         patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):

        res = client.get("/api/analytics?from=2026-01-15&to=2026-01-15&cutoff_rule=day_ahead_1700")
        assert res.status_code == 200
        data = res.json()

        assert data["date_from"] == "2026-01-15"
        assert data["date_to"] == "2026-01-15"
        assert len(data["daily_breakdown"]) == 1
        assert data["aggregate_metrics"]["matched_intervals"] == 24


def test_e2e_journey_forecast_evolution(mock_elexon_fixtures):
    """
    User Journey 5: Trading analyst inspects publication history and gate closure convergence.
    """
    _, forecasts_df = mock_elexon_fixtures

    with patch("app.api.routes.elexon_client.fetch_wind_forecasts", new=AsyncMock(return_value=forecasts_df)):
        res = client.get("/api/forecast-evolution?date=2026-01-15&interval_start=2026-01-15T12:00:00Z")
        assert res.status_code == 200
        data = res.json()

        assert data["delivery_date"] == "2026-01-15"
        assert len(data["revisions"]) > 0

        # Verify at least one revision is pre-cutoff and selected
        pre_cutoffs = [r for r in data["revisions"] if r["is_pre_cutoff"]]
        assert len(pre_cutoffs) > 0
        assert data["selected_publish_time"] is not None
        assert data["selected_forecast_mw"] is not None


def test_e2e_journey_boundary_validation():
    """
    User Journey 6: Boundary validation strictly prevents out-of-pilot queries.
    """
    # Query 2025-12-31 (Before pilot window)
    res_dec = client.get("/api/dashboard?date=2025-12-31")
    assert res_dec.status_code == 400
    assert "restricted" in res_dec.json()["detail"].lower()

    # Query 2026-02-01 (After pilot window)
    res_feb = client.get("/api/dashboard?date=2026-02-01")
    assert res_feb.status_code == 400
    assert "restricted" in res_feb.json()["detail"].lower()

