import React from 'react';
import { MetricsSummary } from '../types';

interface CoverageSummaryProps {
  metrics: MetricsSummary;
  hourlyExpansion: boolean;
}

export const CoverageSummary: React.FC<CoverageSummaryProps> = ({ metrics, hourlyExpansion }) => {
  const coveragePercent = metrics.total_expected > 0
    ? ((metrics.matched_intervals / metrics.total_expected) * 100).toFixed(1)
    : '0';

  return (
    <div
      style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '24px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)'
      }}
    >
      <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '10px' }}>
        <div>
          <span style={{ color: '#94a3b8', fontSize: '13px' }}>Data Coverage: </span>
          <strong style={{ color: '#38bdf8', fontSize: '15px' }}>{coveragePercent}%</strong>
          <span style={{ color: '#64748b', fontSize: '12px' }}> ({metrics.matched_intervals} of {metrics.total_expected} intervals matched)</span>
        </div>
        <div>
          <span style={{ color: '#94a3b8', fontSize: '13px' }}>Missing Forecasts: </span>
          <strong style={{ color: metrics.missing_forecasts > 0 ? '#fbbf24' : '#4ade80', fontSize: '15px' }}>
            {metrics.missing_forecasts}
          </strong>
        </div>
        <div>
          <span style={{ color: '#94a3b8', fontSize: '13px' }}>Missing Actuals: </span>
          <strong style={{ color: metrics.missing_actuals > 0 ? '#f87171' : '#4ade80', fontSize: '15px' }}>
            {metrics.missing_actuals}
          </strong>
        </div>
      </div>

      {/* Progress / Coverage Bar */}
      <div style={{ width: '100%', height: '6px', backgroundColor: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${coveragePercent}%`,
            height: '100%',
            backgroundColor: '#0284c7',
            transition: 'width 0.3s ease-in-out'
          }}
        />
      </div>

      {!hourlyExpansion && metrics.missing_forecasts > 0 && (
        <div style={{ marginTop: '10px', fontSize: '12px', color: '#94a3b8', lineHeight: '1.4' }}>
          💡 <em>Note on 50% Coverage:</em> Elexon <code>WINDFOR</code> forecasts are published at hourly resolution (:00), while settlement intervals occur every 30 minutes. Strict matching pairs 24 on-the-hour intervals. Toggle <strong>"Expand hourly forecast"</strong> above if you wish to apply the hourly forecast across both half-hours of each delivery hour.
        </div>
      )}
    </div>
  );
};
