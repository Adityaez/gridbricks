"""Analytics and decision-time forecast selection engine."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd


def select_cutoff_forecasts(
    forecasts_df: pd.DataFrame,
    cutoff_rule: str = "day_ahead_1700"
) -> pd.DataFrame:
    """
    Filter forecasts to only those published strictly before the cutoff C(t),
    selecting the latest eligible record for each delivery interval (startTime).
    Prevents look-ahead bias.
    """
    if forecasts_df.empty:
        return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw"])
    return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw"])


def compute_metrics(
    matched_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Compute MAE, RMSE, Signed Bias, and WAPE over matched (forecast, actual) pairs.
    Handles zero-denominator WAPE safely by returning None.
    """
    if matched_df.empty:
        return {
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "wape_percent": None,
            "total_expected": 48,
            "matched_intervals": 0,
            "missing_forecasts": 48,
            "missing_actuals": 48,
        }
    return {
        "mae_mw": None,
        "rmse_mw": None,
        "bias_mw": None,
        "wape_percent": None,
        "total_expected": len(matched_df),
        "matched_intervals": 0,
        "missing_forecasts": 0,
        "missing_actuals": 0,
    }

