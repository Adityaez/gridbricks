"""Tests validating the live Elexon API fixtures for January 2026."""
import json
import os
import pytest
import pandas as pd

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_fuelhh_fixture_schema():
    """Verify FUELHH fixture structure, wind records count, and generation units."""
    fixture_path = os.path.join(FIXTURES_DIR, "fuelhh_2026_01_15.json")
    assert os.path.exists(fixture_path), "FUELHH fixture file must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    df = pd.DataFrame(records)
    assert not df.empty
    assert "fuelType" in df.columns
    assert "generation" in df.columns
    assert "startTime" in df.columns
    assert "settlementPeriod" in df.columns

    # Filter for wind
    wind_df = df[df["fuelType"].str.upper() == "WIND"]
    assert len(wind_df) == 48, "Must have exactly 48 half-hour settlement periods of wind actuals"

    # Validate generation values are non-negative numeric
    assert (wind_df["generation"] >= 0).all()

    # Validate timestamps are parseable as UTC
    parsed_start = pd.to_datetime(wind_df["startTime"], utc=True)
    assert parsed_start.dt.tz is not None
    assert str(parsed_start.dt.date.iloc[0]) == "2026-01-15"


def test_windfor_fixture_schema():
    """Verify WINDFOR fixture structure, forecast timestamps, and non-negative generation."""
    fixture_path = os.path.join(FIXTURES_DIR, "windfor_2026_01_15.json")
    assert os.path.exists(fixture_path), "WINDFOR fixture file must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    df = pd.DataFrame(records)
    assert not df.empty
    assert "publishTime" in df.columns
    assert "startTime" in df.columns
    assert "generation" in df.columns

    # Check timestamps parseable as UTC
    parsed_publish = pd.to_datetime(df["publishTime"], utc=True)
    parsed_start = pd.to_datetime(df["startTime"], utc=True)
    assert parsed_publish.dt.tz is not None
    assert parsed_start.dt.tz is not None

    # Check generation is numeric and non-negative
    assert (df["generation"] >= 0).all()
