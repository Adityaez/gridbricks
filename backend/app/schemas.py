"""Pydantic schemas for data transfer objects and API contracts."""
from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class IntervalDataPoint(BaseModel):
    interval_start: datetime = Field(..., description="Start of the half-hour delivery interval in UTC")
    interval_end: datetime = Field(..., description="End of the half-hour delivery interval in UTC")
    settlement_period: int = Field(..., ge=1, le=50, description="UK Settlement Period (1 to 48 or 50)")
    forecast_mw: Optional[float] = Field(None, description="Selected decision-time forecast in MW")
    publish_time: Optional[datetime] = Field(None, description="Publication timestamp of the selected forecast")
    actual_mw: Optional[float] = Field(None, description="Actual realized wind generation from FUELHH in MW")
    error_mw: Optional[float] = Field(None, description="Signed error (forecast - actual) in MW")
    status: Literal["MATCHED", "MISSING_FORECAST", "MISSING_ACTUAL", "MISSING_BOTH"] = Field(
        ..., description="Data matching and availability classification"
    )


class MetricsSummary(BaseModel):
    mae_mw: Optional[float] = Field(None, description="Mean Absolute Error in MW")
    rmse_mw: Optional[float] = Field(None, description="Root Mean Squared Error in MW")
    bias_mw: Optional[float] = Field(None, description="Signed Mean Bias (forecast - actual) in MW")
    wape_percent: Optional[float] = Field(None, description="Weighted Absolute Percentage Error in %")
    total_expected: int = Field(..., description="Total expected intervals in the selected window")
    matched_intervals: int = Field(..., description="Number of intervals with both valid actual and forecast")
    missing_forecasts: int = Field(..., description="Number of intervals lacking eligible pre-cutoff forecast")
    missing_actuals: int = Field(..., description="Number of intervals lacking actual generation")


class DashboardResponse(BaseModel):
    delivery_date: date
    cutoff_rule: str
    metrics: MetricsSummary
    intervals: List[IntervalDataPoint]


class DailyMetricItem(BaseModel):
    delivery_date: date
    metrics: MetricsSummary


class AggregateAnalyticsResponse(BaseModel):
    date_from: date
    date_to: date
    aggregate_metrics: MetricsSummary
    daily_breakdown: List[DailyMetricItem]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
