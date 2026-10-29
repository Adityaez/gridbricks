import { DashboardResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchDashboard(date: string, cutoffRule: string = 'day_ahead_1700'): Promise<DashboardResponse> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard?date=${date}&cutoff_rule=${cutoffRule}`);
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: 'Network response was not ok' }));
    throw new Error(errorBody.detail || `HTTP Error ${response.status}`);
  }
  return response.json();
}

