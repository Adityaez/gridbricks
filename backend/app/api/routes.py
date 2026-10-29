"""FastAPI router endpoints for WindSight dashboard and analytics."""
from datetime import date, datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from app.config import settings
from app.schemas import (
    DashboardResponse,
    HealthResponse,
    AggregateAnalyticsResponse,
    MetricsSummary
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Verify backend health and operational version."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION
    )


@router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
async def get_dashboard(
    delivery_date: date = Query(
        ...,
        alias="date",
        description="Target delivery date in January 2026 (YYYY-MM-DD)"
    ),
    cutoff_rule: str = Query(
        "day_ahead_1700",
        description="Cutoff strategy: day_ahead_1700, gate_closure, fixed_lead_hours"
    )
):
    """
    Retrieve interval-by-interval forecast vs actual data and daily accuracy metrics.
    Restricted strictly to January 2026.
    """
    if str(delivery_date) < settings.START_DATE_LIMIT or str(delivery_date) > settings.END_DATE_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"WindSight pilot scope is restricted to {settings.START_DATE_LIMIT} to {settings.END_DATE_LIMIT}."
        )

    # Return structure template for Phase 0
    return DashboardResponse(
        delivery_date=delivery_date,
        cutoff_rule=cutoff_rule,
        metrics=MetricsSummary(
            mae_mw=None,
            rmse_mw=None,
            bias_mw=None,
            wape_percent=None,
            total_expected=48,
            matched_intervals=0,
            missing_forecasts=48,
            missing_actuals=48
        ),
        intervals=[]
    )
