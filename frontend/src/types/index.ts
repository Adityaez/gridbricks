export type DataStatus = "MATCHED" | "MISSING_FORECAST" | "MISSING_ACTUAL" | "MISSING_BOTH";

export interface IntervalDataPoint {
  interval_start: string;
  interval_end: string;
  settlement_period: number;
  forecast_mw: number | null;
  publish_time: string | null;
  actual_mw: number | null;
  error_mw: number | null;
  status: DataStatus;
}

export interface MetricsSummary {
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  wape_percent: number | null;
  total_expected: number;
  matched_intervals: number;
  missing_forecasts: number;
  missing_actuals: number;
}

export interface DashboardResponse {
  delivery_date: string;
  cutoff_rule: string;
  hourly_expansion: boolean;
  metrics: MetricsSummary;
  intervals: IntervalDataPoint[];
}

export interface DailyMetricItem {
  delivery_date: string;
  metrics: MetricsSummary;
}

export interface AggregateAnalyticsResponse {
  date_from: string;
  date_to: string;
  cutoff_rule: string;
  aggregate_metrics: MetricsSummary;
  daily_breakdown: DailyMetricItem[];
}

export interface ForecastEvolutionPoint {
  publish_time: string;
  forecast_mw: number;
  cutoff_time: string;
  is_pre_cutoff: boolean;
}

export interface ForecastEvolutionResponse {
  delivery_date: string;
  interval_start: string;
  cutoff_rule: string;
  cutoff_time: string;
  selected_publish_time: string | null;
  selected_forecast_mw: number | null;
  revisions: ForecastEvolutionPoint[];
}
