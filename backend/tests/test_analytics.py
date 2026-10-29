"""Unit tests for cutoff selection, look-ahead bias prevention, and metric calculations."""
import json
import os
from datetime import date, datetime, timezone
import pytest
import pandas as pd
from app.services.analytics import (
    calculate_cutoff_timestamp,
    generate_expected_settlement_grid,
    select_cutoff_forecasts,
    compute_metrics,
    build_interval_dashboard
)
from app.services.elexon import ElexonClient

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_calculate_cutoff_timestamp_day_ahead_1700():
    """Verify Day-Ahead 17:00 UTC cutoff on D-1."""
    interval_start = pd.Timestamp("2026-01-15T12:00:00Z")
    cutoff = calculate_cutoff_timestamp(interval_start, cutoff_rule="day_ahead_1700")
    expected = pd.Timestamp("2026-01-14T17:00:00Z")
    assert cutoff == expected


def test_calculate_cutoff_timestamp_gate_closure():
    """Verify gate closure cutoff at t - 1 hour."""
    interval_start = pd.Timestamp("2026-01-15T12:00:00Z")
    cutoff = calculate_cutoff_timestamp(interval_start, cutoff_rule="gate_closure")
    expected = pd.Timestamp("2026-01-15T11:00:00Z")
    assert cutoff == expected


def test_calculate_cutoff_timestamp_fixed_lead():
    """Verify fixed lead cutoff (e.g. fixed_4h at t - 4 hours)."""
    interval_start = pd.Timestamp("2026-01-15T12:00:00Z")
    cutoff = calculate_cutoff_timestamp(interval_start, cutoff_rule="fixed_4h")
    expected = pd.Timestamp("2026-01-15T08:00:00Z")
    assert cutoff == expected


def test_future_forecast_after_cutoff_is_excluded():
    """
    Test 1: Look-Ahead Bias Prevention.
    A forecast published strictly after the cutoff must never be selected.
    """
    interval_start = pd.Timestamp("2026-01-15T12:00:00Z")
    cutoff = pd.Timestamp("2026-01-14T17:00:00Z")

    forecasts = pd.DataFrame([
        # Published 5 mins late: must be excluded
        {"startTime": interval_start, "publishTime": "2026-01-14T17:05:00Z", "generation": 12000},
        # Published way late: must be excluded
        {"startTime": interval_start, "publishTime": "2026-01-15T06:00:00Z", "generation": 13000},
    ])
    result = select_cutoff_forecasts(forecasts, cutoff_rule="day_ahead_1700")
    assert result.empty, "Late forecasts published after cutoff must be excluded entirely"


def test_latest_pre_cutoff_forecast_selected():
    """
    Test 2: When multiple valid forecasts exist before cutoff, select latest.
    """
    interval_start = pd.Timestamp("2026-01-15T12:00:00Z")

    forecasts = pd.DataFrame([
        {"startTime": interval_start, "publishTime": "2026-01-14T06:00:00Z", "generation": 9000},
        {"startTime": interval_start, "publishTime": "2026-01-14T12:00:00Z", "generation": 9500},
        # Latest eligible forecast before 17:00 UTC
        {"startTime": interval_start, "publishTime": "2026-01-14T16:30:00Z", "generation": 9800},
        # Ineligible forecast (after 17:00 UTC)
        {"startTime": interval_start, "publishTime": "2026-01-14T18:00:00Z", "generation": 11000},
    ])
    result = select_cutoff_forecasts(forecasts, cutoff_rule="day_ahead_1700")
    assert len(result) == 1
    assert result.iloc[0]["forecast_mw"] == 9800.0
    assert result.iloc[0]["publishTime"] == pd.Timestamp("2026-01-14T16:30:00Z")


def test_standard_metrics_hand_calculated_vector():
    """
    Test 3: Standard metrics against hand-calculated verification vector.
    F = [100, 200, 300], A = [120, 180, 300]
    e = [-20, +20, 0]
    MAE = 40 / 3 = 13.33
    RMSE = sqrt(800 / 3) = 16.33
    Bias = 0.00
    WAPE = 40 / 600 * 100 = 6.67%
    """
    df = pd.DataFrame({
        "forecast_mw": [100.0, 200.0, 300.0],
        "actual_mw": [120.0, 180.0, 300.0],
        "status": ["MATCHED", "MATCHED", "MATCHED"]
    })
    metrics = compute_metrics(df, total_expected=3)

    assert metrics["matched_intervals"] == 3
    assert metrics["mae_mw"] == 13.33
    assert metrics["rmse_mw"] == 16.33
    assert metrics["bias_mw"] == 0.0
    assert metrics["wape_percent"] == 6.67


def test_wape_zero_denominator_returns_none():
    """
    Test 4: Safe handling of zero actual generation denominator.
    When sum(actual) == 0, WAPE is undefined and must return None (JSON null).
    """
    df = pd.DataFrame({
        "forecast_mw": [10.0, 20.0],
        "actual_mw": [0.0, 0.0],
        "status": ["MATCHED", "MATCHED"]
    })
    metrics = compute_metrics(df, total_expected=2)

    assert metrics["matched_intervals"] == 2
    assert metrics["mae_mw"] == 15.0
    assert metrics["wape_percent"] is None


def test_incomplete_day_and_missing_intervals():
    """
    Test 5: Handle missing actuals, missing forecasts, and partial coverage.
    """
    df = pd.DataFrame({
        "forecast_mw": [100.0, None, 200.0, None],
        "actual_mw": [110.0, 150.0, None, None],
        "status": ["MATCHED", "MISSING_FORECAST", "MISSING_ACTUAL", "MISSING_BOTH"]
    })
    metrics = compute_metrics(df, total_expected=4)

    # Only 1 matched pair should be included in accuracy metrics
    assert metrics["matched_intervals"] == 1
    assert metrics["missing_forecasts"] == 2
    assert metrics["missing_actuals"] == 2
    assert metrics["mae_mw"] == 10.0
    assert metrics["rmse_mw"] == 10.0
    assert metrics["bias_mw"] == -10.0


def test_generate_expected_settlement_grid():
    """Verify 48 settlement periods generated for any date."""
    target_date = date(2026, 1, 15)
    grid = generate_expected_settlement_grid(target_date)

    assert len(grid) == 48
    assert grid.iloc[0]["settlement_period"] == 1
    assert grid.iloc[0]["interval_start"] == pd.Timestamp("2026-01-15T00:00:00Z")
    assert grid.iloc[-1]["settlement_period"] == 48
    assert grid.iloc[-1]["interval_end"] == pd.Timestamp("2026-01-16T00:00:00Z")


def test_hourly_expansion_option():
    """Verify allow_hourly_expansion expands hourly forecast to :30 interval."""
    target_date = date(2026, 1, 15)
    actuals = pd.DataFrame([
        {"startTime": "2026-01-15T00:00:00Z", "actual_mw": 1000.0, "fuelType": "WIND"},
        {"startTime": "2026-01-15T00:30:00Z", "actual_mw": 1100.0, "fuelType": "WIND"},
    ])
    forecasts = pd.DataFrame([
        # Only hourly forecast published
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T12:00:00Z", "generation": 1050.0}
    ])

    # Strict matching (default)
    df_strict, metrics_strict = build_interval_dashboard(
        target_date, actuals, forecasts, cutoff_rule="day_ahead_1700", allow_hourly_expansion=False
    )
    assert df_strict.iloc[0]["status"] == "MATCHED"
    assert df_strict.iloc[1]["status"] == "MISSING_FORECAST"

    # Expanded matching
    df_expanded, metrics_expanded = build_interval_dashboard(
        target_date, actuals, forecasts, cutoff_rule="day_ahead_1700", allow_hourly_expansion=True
    )
    assert df_expanded.iloc[0]["status"] == "MATCHED"
    assert df_expanded.iloc[1]["status"] == "MATCHED"
    assert df_expanded.iloc[1]["forecast_mw"] == 1050.0


def test_real_fixtures_dashboard_build():
    """Integration test: build dashboard from live Jan 15 2026 fixtures."""
    client = ElexonClient()
    target_date = date(2026, 1, 15)

    with open(os.path.join(FIXTURES_DIR, "fuelhh_2026_01_15.json"), "r", encoding="utf-8") as f:
        fuelhh_raw = json.load(f)
    with open(os.path.join(FIXTURES_DIR, "windfor_2026_01_15.json"), "r", encoding="utf-8") as f:
        windfor_raw = json.load(f)

    actuals_df = client.normalize_fuelhh(fuelhh_raw)
    forecasts_df = client.normalize_windfor(windfor_raw, start_date=target_date, end_date=target_date)

    intervals_df, metrics = build_interval_dashboard(
        delivery_date=target_date,
        actuals_df=actuals_df,
        forecasts_df=forecasts_df,
        cutoff_rule="day_ahead_1700",
        allow_hourly_expansion=False
    )

    assert len(intervals_df) == 48
    # 24 on-the-hour intervals matched under strict matching
    assert metrics["matched_intervals"] == 24
    assert metrics["missing_forecasts"] == 24
    assert metrics["missing_actuals"] == 0
    assert metrics["mae_mw"] is not None and metrics["mae_mw"] > 0
    assert metrics["rmse_mw"] is not None and metrics["rmse_mw"] > 0
    assert metrics["wape_percent"] is not None and metrics["wape_percent"] > 0


def test_empty_dataframe_and_fallback_branches():
    """Verify empty inputs, naive timestamps, and unknown cutoff rule fallbacks."""
    # Test naive timestamp conversion
    naive_dt = pd.Timestamp("2026-01-15T12:00:00")
    cutoff = calculate_cutoff_timestamp(naive_dt, cutoff_rule="day_ahead_1700")
    assert cutoff == pd.Timestamp("2026-01-14T17:00:00Z")

    # Test unknown rule fallback
    fallback_cutoff = calculate_cutoff_timestamp(naive_dt, cutoff_rule="unknown_strategy")
    assert fallback_cutoff == pd.Timestamp("2026-01-14T17:00:00Z")

    # Test invalid fixed rule fallback
    invalid_fixed = calculate_cutoff_timestamp(naive_dt, cutoff_rule="fixed_badh")
    assert invalid_fixed == pd.Timestamp("2026-01-14T17:00:00Z")

    # Test empty forecasts in select_cutoff_forecasts
    empty_fc = select_cutoff_forecasts(pd.DataFrame())
    assert empty_fc.empty

    # Test compute_metrics on empty DataFrame
    empty_metrics = compute_metrics(pd.DataFrame())
    assert empty_metrics["mae_mw"] is None
    assert empty_metrics["matched_intervals"] == 0

    # Test dashboard with empty actuals and empty forecasts
    target_date = date(2026, 1, 15)
    df_empty, metrics_empty = build_interval_dashboard(
        delivery_date=target_date,
        actuals_df=pd.DataFrame(),
        forecasts_df=pd.DataFrame()
    )
    assert len(df_empty) == 48
    assert (df_empty["status"] == "MISSING_BOTH").all()
    assert metrics_empty["matched_intervals"] == 0
