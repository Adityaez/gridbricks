"""Unit tests for Elexon BMRS ingestion, normalization, and caching."""
import json
import os
from datetime import date
import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.elexon import ElexonClient

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fuelhh_raw():
    path = os.path.join(FIXTURES_DIR, "fuelhh_2026_01_15.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def windfor_raw():
    path = os.path.join(FIXTURES_DIR, "windfor_2026_01_15.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_normalize_fuelhh_real_fixture(fuelhh_raw):
    """Test FUELHH normalization on real January 15, 2026 data."""
    client = ElexonClient()
    df = client.normalize_fuelhh(fuelhh_raw)

    assert not df.empty
    # Must have 48 settlement periods
    assert len(df) == 48
    # All fuelType must be WIND
    assert (df["fuelType"] == "WIND").all()
    # Generation must be positive and named actual_mw
    assert "actual_mw" in df.columns
    assert (df["actual_mw"] >= 0).all()
    # Timestamps in UTC
    assert df["startTime"].dt.tz is not None
    # Verify settlement periods 1 to 48 are present
    assert set(df["settlementPeriod"]) == set(range(1, 49))


def test_normalize_fuelhh_filtering_and_deduplication():
    """Verify non-wind records are rejected and duplicates are deduplicated."""
    client = ElexonClient()
    raw = [
        {"startTime": "2026-01-01T00:00:00Z", "generation": 100, "fuelType": "COAL"},
        {"startTime": "2026-01-01T00:00:00Z", "generation": 250, "fuelType": "WIND", "publishTime": "2026-01-01T00:30:00Z"},
        # Duplicate with later publishTime
        {"startTime": "2026-01-01T00:00:00Z", "generation": 260, "fuelType": "WIND", "publishTime": "2026-01-01T01:00:00Z"},
        {"startTime": "2026-01-01T00:30:00Z", "generation": -10, "fuelType": "WIND"},  # Negative should be dropped
        {"startTime": "2026-01-01T01:00:00Z", "generation": "invalid", "fuelType": "WIND"},  # Invalid should be dropped
    ]
    df = client.normalize_fuelhh(raw)
    assert len(df) == 1
    assert df.iloc[0]["actual_mw"] == 260.0


def test_normalize_fuelhh_empty_and_missing_fields():
    client = ElexonClient()
    empty_df = client.normalize_fuelhh([])
    assert empty_df.empty
    assert list(empty_df.columns) == ["startTime", "publishTime", "settlementDate", "settlementPeriod", "fuelType", "actual_mw"]

    with pytest.raises(ValueError):
        client.normalize_fuelhh([{"wrongField": 123}])


def test_normalize_windfor_real_fixture(windfor_raw):
    """Test WINDFOR normalization filtering to specific delivery date."""
    client = ElexonClient()
    target_date = date(2026, 1, 15)
    df = client.normalize_windfor(windfor_raw, start_date=target_date, end_date=target_date)

    assert not df.empty
    assert "forecast_mw" in df.columns
    assert (df["forecast_mw"] >= 0).all()

    # All startTimes should fall strictly on 2026-01-15
    delivery_dates = df["startTime"].dt.date.unique()
    assert len(delivery_dates) == 1
    assert delivery_dates[0] == target_date

    # Timestamps in UTC
    assert df["startTime"].dt.tz is not None
    assert df["publishTime"].dt.tz is not None


def test_normalize_windfor_deduplication():
    client = ElexonClient()
    raw = [
        {"startTime": "2026-01-15T12:00:00Z", "publishTime": "2026-01-14T10:00:00Z", "generation": 5000},
        {"startTime": "2026-01-15T12:00:00Z", "publishTime": "2026-01-14T10:00:00Z", "generation": 5500},  # duplicate
    ]
    df = client.normalize_windfor(raw)
    assert len(df) == 1
    assert df.iloc[0]["forecast_mw"] == 5500.0


def test_client_caching(fuelhh_raw):
    """Verify that cached data is returned on subsequent calls."""
    import asyncio

    async def _run():
        client = ElexonClient()
        target_date = date(2026, 1, 15)

        with patch.object(client, "_execute_request_with_retry", new=AsyncMock(return_value=fuelhh_raw)) as mock_req:
            # First call fetches from remote
            df1 = await client.fetch_actual_wind(target_date, target_date)
            assert mock_req.call_count == 1
            assert len(df1) == 48

            # Second call hits cache
            df2 = await client.fetch_actual_wind(target_date, target_date)
            assert mock_req.call_count == 1
            assert len(df2) == 48

            # After clearing cache, next call refetches
            client.clear_cache()
            df3 = await client.fetch_actual_wind(target_date, target_date)
            assert mock_req.call_count == 2

    asyncio.run(_run())


def test_retry_on_server_error():
    """Verify that ElexonClient retries on transient HTTP 500 error."""
    import asyncio
    from unittest.mock import patch, MagicMock
    import httpx

    async def _run():
        client = ElexonClient(max_retries=3, timeout_seconds=2.0)
        
        # Mock httpx response sequence: first 500, then 200
        mock_resp_500 = MagicMock()
        mock_resp_500.status_code = 500

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = []

        with patch("httpx.AsyncClient.get", side_effect=[mock_resp_500, mock_resp_200]) as mock_get:
            result = await client._execute_request_with_retry("datasets/FUELHH/stream", {})
            assert result == []
            assert mock_get.call_count == 2

    asyncio.run(_run())
