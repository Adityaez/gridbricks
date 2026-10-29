"""Analytics engine for decision-time forecast selection and accuracy evaluation."""
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def calculate_cutoff_timestamp(
    interval_start: pd.Timestamp,
    cutoff_rule: str = "day_ahead_1700"
) -> pd.Timestamp:
    """
    Calculate the exact decision cutoff timestamp C(t) for a delivery interval starting at t.

    Strategies:
    - 'day_ahead_1700': D-1 at 17:00:00 UTC (where D is the delivery date of interval_start).
    - 'gate_closure': t - 1 hour (standard UK balancing mechanism gate closure).
    - 'fixed_Xh': t - X hours (e.g., 'fixed_4h' -> t - 4 hours).
    """
    if interval_start.tzinfo is None:
        interval_start = interval_start.tz_localize(timezone.utc)
    else:
        interval_start = interval_start.tz_convert(timezone.utc)

    rule = cutoff_rule.lower().strip()

    if rule == "day_ahead_1700":
        delivery_date = interval_start.date()
        cutoff_date = delivery_date - timedelta(days=1)
        return pd.Timestamp(
            datetime.combine(cutoff_date, time(17, 0, 0), tzinfo=timezone.utc)
        )
    elif rule == "gate_closure":
        return interval_start - pd.Timedelta(hours=1)
    elif rule.startswith("fixed_") and rule.endswith("h"):
        try:
            hours = int(rule.replace("fixed_", "").replace("h", ""))
            return interval_start - pd.Timedelta(hours=hours)
        except ValueError:
            pass

    # Default fallback to day_ahead_1700
    delivery_date = interval_start.date()
    cutoff_date = delivery_date - timedelta(days=1)
    return pd.Timestamp(
        datetime.combine(cutoff_date, time(17, 0, 0), tzinfo=timezone.utc)
    )


def generate_expected_settlement_grid(delivery_date: date) -> pd.DataFrame:
    """
    Generate the standard 48 half-hour UK settlement intervals for a given calendar date.

    Returns DataFrame columns:
        - settlement_period: int (1..48)
        - interval_start: datetime64[ns, UTC]
        - interval_end: datetime64[ns, UTC]
    """
    start_dt = datetime.combine(delivery_date, time(0, 0, 0), tzinfo=timezone.utc)
    intervals = []
    for sp in range(1, 49):
        sp_start = start_dt + timedelta(minutes=30 * (sp - 1))
        sp_end = sp_start + timedelta(minutes=30)
        intervals.append({
            "settlement_period": sp,
            "interval_start": pd.Timestamp(sp_start),
            "interval_end": pd.Timestamp(sp_end)
        })

    return pd.DataFrame(intervals)


def select_cutoff_forecasts(
    forecasts_df: pd.DataFrame,
    cutoff_rule: str = "day_ahead_1700"
) -> pd.DataFrame:
    """
    Filter forecasts to only those published strictly on or before decision cutoff C(t),
    selecting the latest eligible record for each delivery interval (startTime).

    Crucial: Prevents look-ahead bias by excluding any forecast published after C(t).
    """
    if forecasts_df.empty:
        return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw"])

    df = forecasts_df.copy()

    # Ensure UTC timestamps
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)

    # Standardize forecast column name
    if "forecast_mw" not in df.columns and "generation" in df.columns:
        df["forecast_mw"] = pd.to_numeric(df["generation"], errors="coerce")
    elif "forecast_mw" in df.columns:
        df["forecast_mw"] = pd.to_numeric(df["forecast_mw"], errors="coerce")

    # Calculate cutoff C(t) for each delivery interval
    # Cache unique startTimes for performance
    unique_starts = df["startTime"].unique()
    cutoff_map = {
        st: calculate_cutoff_timestamp(st, cutoff_rule)
        for st in unique_starts
    }
    df["cutoff_time"] = df["startTime"].map(cutoff_map)

    # Filter: publishTime <= C(t)
    eligible = df[df["publishTime"] <= df["cutoff_time"]].copy()
    if eligible.empty:
        return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw"])

    # For each delivery interval startTime, select latest publishTime
    # Sort by startTime and publishTime ascending, then drop_duplicates keeping last
    eligible = eligible.sort_values(by=["startTime", "publishTime"])
    latest_eligible = eligible.drop_duplicates(subset=["startTime"], keep="last").reset_index(drop=True)

    return latest_eligible[["startTime", "publishTime", "forecast_mw"]]


def compute_metrics(
    intervals_df: pd.DataFrame,
    total_expected: int = 48
) -> Dict[str, Any]:
    """
    Compute MAE, RMSE, Signed Bias, and WAPE over matched (forecast, actual) pairs.
    Handles zero-denominator WAPE safely by returning None.

    Formulas:
        Signed error: F - A
        MAE: mean(|F - A|)
        RMSE: sqrt(mean((F - A)^2))
        Bias: mean(F - A)
        WAPE: sum(|F - A|) / sum(A) * 100  (if sum(A) > 0, else None)
    """
    if intervals_df.empty:
        return {
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "wape_percent": None,
            "total_expected": total_expected,
            "matched_intervals": 0,
            "missing_forecasts": total_expected,
            "missing_actuals": total_expected,
        }

    # Filter to MATCHED status rows (or where both values exist and are numeric)
    matched = intervals_df[
        intervals_df["actual_mw"].notna() &
        intervals_df["forecast_mw"].notna()
    ].copy()

    n = len(matched)
    missing_forecasts = int(intervals_df["forecast_mw"].isna().sum())
    missing_actuals = int(intervals_df["actual_mw"].isna().sum())

    if n == 0:
        return {
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "wape_percent": None,
            "total_expected": total_expected,
            "matched_intervals": 0,
            "missing_forecasts": missing_forecasts,
            "missing_actuals": missing_actuals,
        }

    errors = (matched["forecast_mw"] - matched["actual_mw"]).to_numpy(dtype=float)
    actuals = matched["actual_mw"].to_numpy(dtype=float)

    mae = float(np.round(np.mean(np.abs(errors)), 2))
    rmse = float(np.round(np.sqrt(np.mean(np.square(errors))), 2))
    bias = float(np.round(np.mean(errors), 2))

    actual_sum = float(np.sum(actuals))
    if actual_sum > 0:
        wape = float(np.round((np.sum(np.abs(errors)) / actual_sum) * 100.0, 2))
    else:
        wape = None

    return {
        "mae_mw": mae,
        "rmse_mw": rmse,
        "bias_mw": bias,
        "wape_percent": wape,
        "total_expected": total_expected,
        "matched_intervals": n,
        "missing_forecasts": missing_forecasts,
        "missing_actuals": missing_actuals,
    }


def build_interval_dashboard(
    delivery_date: date,
    actuals_df: pd.DataFrame,
    forecasts_df: pd.DataFrame,
    cutoff_rule: str = "day_ahead_1700",
    allow_hourly_expansion: bool = False
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Construct the unified 48 settlement-interval dataset for delivery_date,
    joining realized actual generation with decision-time forecast selections.

    Parameters:
    - delivery_date: Date to evaluate in January 2026.
    - actuals_df: Normalized FUELHH wind actuals DataFrame.
    - forecasts_df: Normalized WINDFOR wind forecasts DataFrame.
    - cutoff_rule: 'day_ahead_1700', 'gate_closure', or 'fixed_Xh'.
    - allow_hourly_expansion: If True, expands hourly WINDFOR forecasts (HH:00) to the
      subsequent half-hour interval (HH:30) of the same delivery hour. If False,
      performs strict timestamp matching (24 matched, 24 missing forecast).

    Returns:
    - (intervals_df, metrics_summary)
    """
    # 1. Base grid of 48 half-hour settlement periods
    grid_df = generate_expected_settlement_grid(delivery_date)

    # 2. Select pre-cutoff forecasts (look-ahead bias protection)
    selected_forecasts = select_cutoff_forecasts(forecasts_df, cutoff_rule)

    # 3. Optional: Expand hourly forecasts to half-hourly intervals
    if allow_hourly_expansion and not selected_forecasts.empty:
        # Create half-hour pairs: HH:00 -> HH:30
        expanded_records = []
        for _, row in selected_forecasts.iterrows():
            st = row["startTime"]
            expanded_records.append({
                "startTime": st,
                "publishTime": row["publishTime"],
                "forecast_mw": row["forecast_mw"]
            })
            # Add HH:30 if st is on the hour
            if st.minute == 0:
                expanded_records.append({
                    "startTime": st + pd.Timedelta(minutes=30),
                    "publishTime": row["publishTime"],
                    "forecast_mw": row["forecast_mw"]
                })
        selected_forecasts = pd.DataFrame(expanded_records).drop_duplicates(subset=["startTime"])

    # 4. Merge grid with actuals
    if not actuals_df.empty:
        actuals_clean = actuals_df.copy()
        actuals_clean["startTime"] = pd.to_datetime(actuals_clean["startTime"], utc=True)
        # Select relevant columns
        cols_to_use = [c for c in ["startTime", "actual_mw", "publishTime"] if c in actuals_clean.columns]
        merged = pd.merge(
            grid_df,
            actuals_clean[cols_to_use].rename(columns={"publishTime": "actual_publishTime"}),
            left_on="interval_start",
            right_on="startTime",
            how="left"
        ).drop(columns=["startTime"], errors="ignore")
    else:
        merged = grid_df.copy()
        merged["actual_mw"] = None

    # 5. Merge with selected forecasts
    if not selected_forecasts.empty:
        merged = pd.merge(
            merged,
            selected_forecasts[["startTime", "publishTime", "forecast_mw"]],
            left_on="interval_start",
            right_on="startTime",
            how="left"
        ).drop(columns=["startTime"], errors="ignore")
    else:
        merged["forecast_mw"] = None
        merged["publishTime"] = None

    # 6. Status classification and signed error calculation
    statuses: List[str] = []
    errors: List[Optional[float]] = []

    for _, row in merged.iterrows():
        has_act = pd.notna(row.get("actual_mw"))
        has_fc = pd.notna(row.get("forecast_mw"))

        if has_act and has_fc:
            status = "MATCHED"
            err = round(float(row["forecast_mw"]) - float(row["actual_mw"]), 2)
        elif has_act and not has_fc:
            status = "MISSING_FORECAST"
            err = None
        elif not has_act and has_fc:
            status = "MISSING_ACTUAL"
            err = None
        else:
            status = "MISSING_BOTH"
            err = None

        statuses.append(status)
        errors.append(err)

    merged["status"] = statuses
    merged["error_mw"] = errors

    # 7. Calculate aggregate summary metrics
    metrics = compute_metrics(merged, total_expected=len(merged))

    return merged, metrics
