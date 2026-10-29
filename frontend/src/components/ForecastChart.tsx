import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { IntervalDataPoint } from '../types';

interface ForecastChartProps {
  data: IntervalDataPoint[];
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div
        style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '10px',
          padding: '40px 20px',
          textAlign: 'center',
          color: '#94a3b8',
          marginBottom: '24px'
        }}
      >
        No interval data available for the selected parameters.
      </div>
    );
  }

  // Format data for Recharts
  const chartData = data.map((item) => {
    const timeLabel = item.interval_start
      ? new Date(item.interval_start).toISOString().substring(11, 16)
      : `SP ${item.settlement_period}`;

    return {
      period: item.settlement_period,
      timeLabel,
      actual: item.actual_mw,
      forecast: item.forecast_mw,
      error: item.error_mw,
      publishTime: item.publish_time
        ? new Date(item.publish_time).toISOString().replace('T', ' ').substring(0, 16)
        : null,
      status: item.status
    };
  });

  // Custom Recharts Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const row = payload[0].payload;
      return (
        <div
          style={{
            backgroundColor: '#0f172a',
            border: '1px solid #475569',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#f8fafc',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.4)',
            minWidth: '200px'
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: '6px', borderBottom: '1px solid #334155', paddingBottom: '4px' }}>
            Period {row.period} ({label} UTC)
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '4px 0' }}>
            <span style={{ color: '#10b981' }}>● Actual Generation:</span>
            <strong>{row.actual !== null ? `${row.actual.toLocaleString()} MW` : 'Missing'}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '4px 0' }}>
            <span style={{ color: '#38bdf8' }}>-- Selected Forecast:</span>
            <strong>{row.forecast !== null ? `${row.forecast.toLocaleString()} MW` : 'Missing'}</strong>
          </div>
          {row.error !== null && (
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '4px 0' }}>
              <span style={{ color: '#cbd5e1' }}>Signed Error (F - A):</span>
              <strong style={{ color: row.error > 0 ? '#fbbf24' : row.error < 0 ? '#60a5fa' : '#cbd5e1' }}>
                {row.error > 0 ? `+${row.error}` : row.error} MW
              </strong>
            </div>
          )}
          {row.publishTime && (
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px', borderTop: '1px solid #334155', paddingTop: '4px' }}>
              Forecast Published: {row.publishTime} UTC
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
          Wind Generation: Realized Actual vs. Day-Ahead Decision Forecast
        </h3>
        <span style={{ fontSize: '12px', color: '#94a3b8' }}>Units: Megawatts (MW)</span>
      </div>

      <div style={{ width: '100%', height: 380 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
            <XAxis
              dataKey="timeLabel"
              stroke="#94a3b8"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              interval={3}
              angle={-25}
              textAnchor="end"
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              tickFormatter={(val) => `${val.toLocaleString()} MW`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ paddingBottom: '12px', fontSize: '12px' }}
            />
            <Line
              type="monotone"
              dataKey="actual"
              name="Realized Actual (FUELHH)"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={{ r: 2, fill: '#10b981' }}
              activeDot={{ r: 5 }}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="forecast"
              name="Decision Forecast (WINDFOR)"
              stroke="#38bdf8"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 2, fill: '#38bdf8' }}
              activeDot={{ r: 5 }}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
