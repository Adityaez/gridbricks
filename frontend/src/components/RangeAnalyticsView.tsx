import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { fetchAnalytics } from '../services/api';
import { AggregateAnalyticsResponse } from '../types';
import { MetricCard } from './MetricCard';

interface RangeAnalyticsViewProps {
  cutoffRule: string;
  hourlyExpansion: boolean;
}

export const RangeAnalyticsView: React.FC<RangeAnalyticsViewProps> = ({ cutoffRule, hourlyExpansion }) => {
  const [fromDate, setFromDate] = useState<string>('2026-01-01');
  const [toDate, setToDate] = useState<string>('2026-01-15');
  const [analyticsData, setAnalyticsData] = useState<AggregateAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAnalytics(fromDate, toDate, cutoffRule, hourlyExpansion);
        if (isMounted) {
          setAnalyticsData(data);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load aggregate analytics');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadAnalytics();
    return () => {
      isMounted = false;
    };
  }, [fromDate, toDate, cutoffRule, hourlyExpansion]);

  const chartData = analyticsData?.daily_breakdown.map((item) => ({
    date: item.delivery_date.substring(5), // '01-15'
    fullDate: item.delivery_date,
    mae: item.metrics.mae_mw,
    bias: item.metrics.bias_mw,
    rmse: item.metrics.rmse_mw,
    wape: item.metrics.wape_percent
  })) || [];

  return (
    <div>
      {/* Date Range Selector */}
      <div
        style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '10px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          gap: '20px',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}
      >
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
            From Date
          </label>
          <input
            type="date"
            min="2026-01-01"
            max="2026-01-31"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '4px',
              padding: '6px 10px',
              fontSize: '13px'
            }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
            To Date
          </label>
          <input
            type="date"
            min="2026-01-01"
            max="2026-01-31"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '4px',
              padding: '6px 10px',
              fontSize: '13px'
            }}
          />
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '12px', color: '#94a3b8' }}>
          Scope: January 2026 Pilot Aggregate
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center', color: '#38bdf8' }}>
          Calculating aggregate accuracy metrics...
        </div>
      ) : error ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#f87171' }}>
          {error}
        </div>
      ) : !analyticsData ? null : (
        <>
          {/* Aggregate Metrics Strip */}
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' }}>
            <MetricCard
              title="Aggregate MAE"
              value={analyticsData.aggregate_metrics.mae_mw}
              unit="MW"
              description="Mean Absolute Error across range"
              formula="MAE = (1/N) * Σ |F - A|"
              color="#38bdf8"
            />
            <MetricCard
              title="Aggregate RMSE"
              value={analyticsData.aggregate_metrics.rmse_mw}
              unit="MW"
              description="Root Mean Squared Error"
              formula="RMSE = sqrt((1/N) * Σ (F - A)^2)"
              color="#818cf8"
            />
            <MetricCard
              title="Aggregate Signed Bias"
              value={analyticsData.aggregate_metrics.bias_mw}
              unit="MW"
              description="Mean Forecast - Actual"
              formula="Bias = (1/N) * Σ (F - A)"
              color={
                analyticsData.aggregate_metrics.bias_mw === null
                  ? '#cbd5e1'
                  : analyticsData.aggregate_metrics.bias_mw > 0
                  ? '#fbbf24'
                  : '#38bdf8'
              }
              badge={
                analyticsData.aggregate_metrics.bias_mw !== null
                  ? analyticsData.aggregate_metrics.bias_mw > 0
                    ? 'Over-Forecast'
                    : 'Under-Forecast'
                  : undefined
              }
            />
            <MetricCard
              title="Aggregate WAPE"
              value={analyticsData.aggregate_metrics.wape_percent}
              unit="%"
              description="Weighted Absolute % Error"
              formula="WAPE = (Σ |F - A| / Σ A) * 100%"
              color="#34d399"
            />
          </div>

          {/* Daily Breakdown Chart */}
          <div
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '10px',
              padding: '20px',
              marginBottom: '24px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)'
            }}
          >
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
              Daily Accuracy Breakdown (MAE &amp; Signed Bias)
            </h3>
            <div style={{ width: '100%', height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
                  <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <Tooltip
                    content={({ active, payload, label }: any) => {
                      if (active && payload && payload.length) {
                        return (
                          <div
                            style={{
                              backgroundColor: '#0f172a',
                              border: '1px solid #475569',
                              padding: '10px 14px',
                              borderRadius: '8px',
                              fontSize: '12px',
                              color: '#f8fafc'
                            }}
                          >
                            <div style={{ fontWeight: 700, marginBottom: '6px' }}>Date: 2026-{label}</div>
                            {payload.map((entry: any) => (
                              <div key={entry.name} style={{ color: entry.color, margin: '2px 0' }}>
                                {entry.name}: {entry.value !== null ? `${entry.value} MW` : 'N/A'}
                              </div>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend verticalAlign="top" align="right" wrapperStyle={{ paddingBottom: '12px', fontSize: '12px' }} />
                  <Bar dataKey="mae" name="Daily MAE (MW)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="bias" name="Daily Signed Bias (MW)" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

