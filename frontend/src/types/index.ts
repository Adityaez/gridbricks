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
  metrics: MetricsSummary;
  intervals: IntervalDataPoint[];
}
