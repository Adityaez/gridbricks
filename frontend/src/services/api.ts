import {
  DashboardResponse,
  AggregateAnalyticsResponse,
  ForecastEvolutionResponse
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function fetchDashboard(
  date: string,
  cutoffRule: string = 'day_ahead_1700',
  hourlyExpansion: boolean = false
): Promise<DashboardResponse> {
  const params = new URLSearchParams({
    date,
    cutoff_rule: cutoffRule,
    hourly_expansion: hourlyExpansion ? 'true' : 'false'
  });
  const res = await fetch(`${API_BASE_URL}/api/dashboard?${params.toString()}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to fetch dashboard data' }));
    throw new Error(errorBody.detail || `HTTP Error ${res.status}`);
  }
  return res.json();
}

export async function fetchAnalytics(
  fromDate: string,
  toDate: string,
  cutoffRule: string = 'day_ahead_1700',
  hourlyExpansion: boolean = false
): Promise<AggregateAnalyticsResponse> {
  const params = new URLSearchParams({
    from: fromDate,
    to: toDate,
    cutoff_rule: cutoffRule,
    hourly_expansion: hourlyExpansion ? 'true' : 'false'
  });
  const res = await fetch(`${API_BASE_URL}/api/analytics?${params.toString()}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to fetch aggregate analytics' }));
    throw new Error(errorBody.detail || `HTTP Error ${res.status}`);
  }
  return res.json();
}

export async function fetchForecastEvolution(
  date: string,
  intervalStart?: string,
  cutoffRule: string = 'day_ahead_1700'
): Promise<ForecastEvolutionResponse> {
  const params = new URLSearchParams({
    date,
    cutoff_rule: cutoffRule
  });
  if (intervalStart) {
    params.set('interval_start', intervalStart);
  }
  const res = await fetch(`${API_BASE_URL}/api/forecast-evolution?${params.toString()}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to fetch forecast evolution' }));
    throw new Error(errorBody.detail || `HTTP Error ${res.status}`);
  }
  return res.json();
}

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) {
    throw new Error('Health check failed');
  }
  return res.json();
}
