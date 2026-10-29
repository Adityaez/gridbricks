import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine
} from 'recharts';
import { fetchForecastEvolution } from '../services/api';
import { ForecastEvolutionResponse } from '../types';

interface ForecastEvolutionChartProps {
  date: string;
  cutoffRule: string;
}

export const ForecastEvolutionChart: React.FC<ForecastEvolutionChartProps> = ({ date, cutoffRule }) => {
  const [evolutionData, setEvolutionData] = useState<ForecastEvolutionResponse | null>(null);
  const [selectedIntervalHour, setSelectedIntervalHour] = useState<string>('12:00:00');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadEvolution = async () => {
      setLoading(true);
      setError(null);
      try {
        const intervalTimestamp = `${date}T${selectedIntervalHour}Z`;
        const res = await fetchForecastEvolution(date, intervalTimestamp, cutoffRule);
        if (isMounted) {
          setEvolutionData(res);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load forecast evolution');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadEvolution();
    return () => {
      isMounted = false;
    };
  }, [date, selectedIntervalHour, cutoffRule]);

  const chartData = evolutionData?.revisions.map((rev) => ({
    timeLabel: new Date(rev.publish_time).toISOString().replace('T', ' ').substring(5, 16),
    publishTime: rev.publish_time,
    forecast: rev.forecast_mw,
    isPreCutoff: rev.is_pre_cutoff
  })) || [];

  const cutoffLabel = evolutionData?.cutoff_time
    ? new Date(evolutionData.cutoff_time).toISOString().replace('T', ' ').substring(5, 16)
    : '';

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
            Forecast Evolution: Revisions Over Time for Delivery Interval
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
            Track how forecasts were updated leading up to gate closure. Highlights the pre-cutoff decision point.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '12px', color: '#94a3b8' }}>Select Hour:</label>
          <select
            value={selectedIntervalHour}
            onChange={(e) => setSelectedIntervalHour(e.target.value)}
            style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '4px',
              padding: '6px 10px',
              fontSize: '12px'
            }}
          >
            {Array.from({ length: 24 }).map((_, i) => {
              const hh = String(i).padStart(2, '0');
              return (
                <option key={hh} value={`${hh}:00:00`}>
                  {hh}:00 UTC
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center', color: '#38bdf8' }}>
          Loading forecast evolution trace...
        </div>
      ) : error ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#f87171' }}>
          {error}
        </div>
      ) : chartData.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
          No historical forecast publications found for this delivery interval.
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', gap: '20px', marginBottom: '14px', flexWrap: 'wrap', fontSize: '12px' }}>
            <div>
              <span style={{ color: '#94a3b8' }}>Cutoff Applied: </span>
              <strong style={{ color: '#f87171' }}>{cutoffLabel} UTC</strong>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Selected Decision Forecast: </span>
              <strong style={{ color: '#38bdf8' }}>
                {evolutionData?.selected_forecast_mw !== null
                  ? `${evolutionData?.selected_forecast_mw.toLocaleString()} MW`
                  : 'None eligible'}
              </strong>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Total Revisions Published: </span>
              <strong style={{ color: '#e2e8f0' }}>{chartData.length}</strong>
            </div>
          </div>

          <div style={{ width: '100%', height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
                <XAxis
                  dataKey="timeLabel"
                  stroke="#94a3b8"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  angle={-25}
                  textAnchor="end"
                />
                <YAxis
                  stroke="#94a3b8"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  tickFormatter={(val) => `${val.toLocaleString()} MW`}
                />
                <Tooltip
                  content={({ active, payload }: any) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
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
                          <div><strong>Published:</strong> {d.publishTime}</div>
                          <div style={{ color: '#38bdf8', marginTop: '4px' }}>
                            <strong>Forecast:</strong> {d.forecast.toLocaleString()} MW
                          </div>
                          <div style={{ color: d.isPreCutoff ? '#34d399' : '#fbbf24', marginTop: '4px' }}>
                            {d.isPreCutoff ? '✓ Eligible (Pre-Cutoff)' : '✗ Excluded (Post-Cutoff Revision)'}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {cutoffLabel && (
                  <ReferenceLine
                    x={cutoffLabel}
                    stroke="#ef4444"
                    strokeDasharray="4 4"
                    label={{ value: 'Decision Cutoff', fill: '#ef4444', fontSize: 11, position: 'top' }}
                  />
                )}
                <Line
                  type="stepAfter"
                  dataKey="forecast"
                  name="Forecast MW"
                  stroke="#38bdf8"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#38bdf8' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
};

