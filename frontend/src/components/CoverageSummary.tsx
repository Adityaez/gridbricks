import React from 'react';
import { MetricsSummary } from '../types';

interface CoverageSummaryProps {
  metrics: MetricsSummary;
}

export const CoverageSummary: React.FC<CoverageSummaryProps> = ({ metrics }) => {
  const coveragePercent = metrics.total_expected > 0 
    ? ((metrics.matched_intervals / metrics.total_expected) * 100).toFixed(1)
    : '0';

  return (
    <div style={{
      backgroundColor: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '8px',
      padding: '16px',
      marginTop: '20px',
      display: 'flex',
      gap: '24px',
      alignItems: 'center',
      flexWrap: 'wrap'
    }}>
      <div>
        <span style={{ color: '#94a3b8', fontSize: '13px' }}>Data Coverage: </span>
        <strong style={{ color: '#38bdf8' }}>{coveragePercent}%</strong> ({metrics.matched_intervals} / {metrics.total_expected} intervals)
      </div>
      <div>
        <span style={{ color: '#94a3b8', fontSize: '13px' }}>Missing Forecasts: </span>
        <strong style={{ color: metrics.missing_forecasts > 0 ? '#f87171' : '#4ade80' }}>{metrics.missing_forecasts}</strong>
      </div>
      <div>
        <span style={{ color: '#94a3b8', fontSize: '13px' }}>Missing Actuals: </span>
        <strong style={{ color: metrics.missing_actuals > 0 ? '#f87171' : '#4ade80' }}>{metrics.missing_actuals}</strong>
      </div>
    </div>
  );
};
