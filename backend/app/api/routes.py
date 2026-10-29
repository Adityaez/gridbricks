"""FastAPI router endpoints for WindSight dashboard, analytics, and forecast evolution."""
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.schemas import (
    AggregateAnalyticsResponse,
    DailyMetricItem,
    DashboardResponse,
    ForecastEvolutionPoint,
    ForecastEvolutionResponse,
    HealthResponse,
    IntervalDataPoint,
    MetricsSummary,
)
from app.services.analytics import (
    build_interval_dashboard,
    calculate_cutoff_timestamp,
    compute_metrics,
)
from app.services.elexon import ElexonClient

router = APIRouter()
elexon_client = ElexonClient()


def validate_date_in_scope(target_date: date, param_name: str = "date") -> None:
    """Ensure date is within the January 2026 historical pilot boundaries."""
    date_str = str(target_date)
    if date_str < settings.START_DATE_LIMIT or date_str > settings.END_DATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Date parameter '{param_name}' ({date_str}) is out of bounds. "
                f"WindSight pilot scope is strictly restricted to {settings.START_DATE_LIMIT} to {settings.END_DATE_LIMIT}."
            ),
        )


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Verify backend health and operational version."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION,
    )


@router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
async def get_dashboard(
    delivery_date: date = Query(
        ...,
        alias="date",
        description="Target delivery date in January 2026 (YYYY-MM-DD)",
    ),
    cutoff_rule: str = Query(
        "day_ahead_1700",
        description="Cutoff strategy: day_ahead_1700, gate_closure, fixed_4h",
    ),
    allow_hourly_expansion: bool = Query(
        False,
        alias="hourly_expansion",
        description="Expand 60-min WINDFOR forecasts across both half-hours of each delivery hour",
    ),
):
    """
    Retrieve interval-by-interval forecast vs actual data, accuracy metrics,
    and missing data coverage for a specific delivery date in January 2026.
    """
    validate_date_in_scope(delivery_date, "date")

    try:
        actuals_df = await elexon_client.fetch_actual_wind(delivery_date, delivery_date)
        forecasts_df = await elexon_client.fetch_wind_forecasts(delivery_date, delivery_date)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch data from Elexon BMRS upstream: {exc}",
        )

    intervals_df, metrics_dict = build_interval_dashboard(
        delivery_date=delivery_date,
        actuals_df=actuals_df,
        forecasts_df=forecasts_df,
        cutoff_rule=cutoff_rule,
        allow_hourly_expansion=allow_hourly_expansion,
    )

    interval_points: List[IntervalDataPoint] = []
    for _, row in intervals_df.iterrows():
        fc_val = float(row["forecast_mw"]) if pd.notna(row.get("forecast_mw")) else None
        act_val = float(row["actual_mw"]) if pd.notna(row.get("actual_mw")) else None
        err_val = float(row["error_mw"]) if pd.notna(row.get("error_mw")) else None
        pub_time = row["publishTime"].to_pydatetime() if pd.notna(row.get("publishTime")) else None

        interval_points.append(
            IntervalDataPoint(
                interval_start=row["interval_start"].to_pydatetime(),
                interval_end=row["interval_end"].to_pydatetime(),
                settlement_period=int(row["settlement_period"]),
                forecast_mw=fc_val,
                publish_time=pub_time,
                actual_mw=act_val,
                error_mw=err_val,
                status=row["status"],
            )
        )

    return DashboardResponse(
        delivery_date=delivery_date,
        cutoff_rule=cutoff_rule,
        hourly_expansion=allow_hourly_expansion,
        metrics=MetricsSummary(**metrics_dict),
        intervals=interval_points,
    )


@router.get("/analytics", response_model=AggregateAnalyticsResponse, tags=["Analytics"])
async def get_analytics(
    from_date: date = Query(
        ...,
        alias="from",
        description="Start delivery date in January 2026 (YYYY-MM-DD)",
    ),
    to_date: date = Query(
        ...,
        alias="to",
        description="End delivery date in January 2026 (YYYY-MM-DD)",
    ),
    cutoff_rule: str = Query(
        "day_ahead_1700",
        description="Cutoff strategy: day_ahead_1700, gate_closure, fixed_4h",
    ),
    allow_hourly_expansion: bool = Query(
        False,
        alias="hourly_expansion",
        description="Expand 60-min WINDFOR forecasts across both half-hours",
    ),
):
    """
    Retrieve aggregated accuracy metrics and daily performance breakdown
    over a delivery date range in January 2026.
    """
    validate_date_in_scope(from_date, "from")
    validate_date_in_scope(to_date, "to")

    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start date 'from' ({from_date}) must be on or before end date 'to' ({to_date}).",
        )

    try:
        actuals_df = await elexon_client.fetch_actual_wind(from_date, to_date)
        forecasts_df = await elexon_client.fetch_wind_forecasts(from_date, to_date)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch upstream Elexon data: {exc}",
        )

    # Process each day sequentially
    current = from_date
    daily_items: List[DailyMetricItem] = []
    all_intervals_list: List[pd.DataFrame] = []

    while current <= to_date:
        # Filter actuals and forecasts for this specific delivery date
        day_start = pd.Timestamp(datetime.combine(current, time.min, tzinfo=timezone.utc))
        day_end = pd.Timestamp(datetime.combine(current, time.max, tzinfo=timezone.utc))

        day_actuals = actuals_df[
            (actuals_df["startTime"] >= day_start) & (actuals_df["startTime"] <= day_end)
        ] if not actuals_df.empty else pd.DataFrame()

        day_forecasts = forecasts_df[
            (forecasts_df["startTime"] >= day_start) & (forecasts_df["startTime"] <= day_end)
        ] if not forecasts_df.empty else pd.DataFrame()

        day_intervals, day_metrics_dict = build_interval_dashboard(
            delivery_date=current,
            actuals_df=day_actuals,
            forecasts_df=day_forecasts,
            cutoff_rule=cutoff_rule,
            allow_hourly_expansion=allow_hourly_expansion,
        )

        daily_items.append(
            DailyMetricItem(
                delivery_date=current,
                metrics=MetricsSummary(**day_metrics_dict),
            )
        )
        all_intervals_list.append(day_intervals)
        current += timedelta(days=1)

    # Calculate overall aggregate metrics across all days
    total_days = (to_date - from_date).days + 1
    total_expected = 48 * total_days
    if all_intervals_list:
        combined_intervals = pd.concat(all_intervals_list, ignore_index=True)
        aggregate_metrics_dict = compute_metrics(combined_intervals, total_expected=total_expected)
    else:
        aggregate_metrics_dict = compute_metrics(pd.DataFrame(), total_expected=total_expected)

    return AggregateAnalyticsResponse(
        date_from=from_date,
        date_to=to_date,
        cutoff_rule=cutoff_rule,
        aggregate_metrics=MetricsSummary(**aggregate_metrics_dict),
        daily_breakdown=daily_items,
    )


@router.get("/forecast-evolution", response_model=ForecastEvolutionResponse, tags=["Analytics"])
async def get_forecast_evolution(
    delivery_date: date = Query(
        ...,
        alias="date",
        description="Target delivery date in January 2026 (YYYY-MM-DD)",
    ),
    interval_start: Optional[datetime] = Query(
        None,
        description="Specific delivery interval start in UTC (default is 12:00:00 UTC)",
    ),
    cutoff_rule: str = Query(
        "day_ahead_1700",
        description="Cutoff strategy: day_ahead_1700, gate_closure, fixed_4h",
    ),
):
    """
    Retrieve the historical publication sequence of forecasts for a specific delivery interval,
    showing how forecasts evolved over time leading up to and past the decision cutoff.
    """
    validate_date_in_scope(delivery_date, "date")

    # If interval_start is not specified, default to 12:00 UTC on delivery_date
    if interval_start is None:
        target_interval = datetime.combine(delivery_date, time(12, 0, 0), tzinfo=timezone.utc)
    else:
        if interval_start.tzinfo is None:
            target_interval = interval_start.replace(tzinfo=timezone.utc)
        else:
            target_interval = interval_start.astimezone(timezone.utc)

    cutoff_time = calculate_cutoff_timestamp(pd.Timestamp(target_interval), cutoff_rule).to_pydatetime()

    try:
        forecasts_df = await elexon_client.fetch_wind_forecasts(delivery_date, delivery_date)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch forecast records from upstream: {exc}",
        )

    # Filter forecasts for target_interval startTime
    target_ts = pd.Timestamp(target_interval)
    matching_fc = forecasts_df[forecasts_df["startTime"] == target_ts].copy()

    revisions: List[ForecastEvolutionPoint] = []
    selected_publish_time: Optional[datetime] = None
    selected_forecast_mw: Optional[float] = None

    if not matching_fc.empty:
        # Sort by publishTime ascending
        matching_fc = matching_fc.sort_values(by="publishTime").reset_index(drop=True)

        for _, row in matching_fc.iterrows():
            pub_dt = row["publishTime"].to_pydatetime()
            is_pre = pub_dt <= cutoff_time
            val = float(row["forecast_mw"])

            revisions.append(
                ForecastEvolutionPoint(
                    publish_time=pub_dt,
                    forecast_mw=val,
                    cutoff_time=cutoff_time,
                    is_pre_cutoff=is_pre,
                )
            )
            # Latest pre-cutoff forecast is the selected one
            if is_pre:
                selected_publish_time = pub_dt
                selected_forecast_mw = val

    return ForecastEvolutionResponse(
        delivery_date=delivery_date,
        interval_start=target_interval,
        cutoff_rule=cutoff_rule,
        cutoff_time=cutoff_time,
        selected_publish_time=selected_publish_time,
        selected_forecast_mw=selected_forecast_mw,
        revisions=revisions,
    )
