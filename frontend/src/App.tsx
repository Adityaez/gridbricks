import React, { useState } from 'react';
import { DateSelector } from './components/DateSelector';
import { MetricCard } from './components/MetricCard';
import { ForecastChart } from './components/ForecastChart';
import { ForecastTable } from './components/ForecastTable';
import { CoverageSummary } from './components/CoverageSummary';
import { MetricsSummary } from './types';

export const App: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('2026-01-15');
  const [cutoffRule, setCutoffRule] = useState<string>('day_ahead_1700');

  // Initial placeholder state for Phase 0
  const initialMetrics: MetricsSummary = {
    mae_mw: null,
    rmse_mw: null,
    bias_mw: null,
    wape_percent: null,
    total_expected: 48,
    matched_intervals: 0,
    missing_forecasts: 48,
    missing_actuals: 48
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 20px' }}>
      <header style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h1 style={{ margin: '0 0 6px 0', fontSize: '24px', color: '#f8fafc' }}>
              WindSight
            </h1>
            <p style={{ margin: 0, fontSize: '14px', color: '#94a3b8' }}>
              Day-Ahead Wind Forecast Intelligence &amp; Accuracy Evaluation
            </p>
          </div>
          <div style={{
            backgroundColor: '#0369a1',
            color: '#f0f9ff',
            padding: '4px 12px',
            borderRadius: '16px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            January 2026 Historical Pilot
          </div>
        </div>
      </header>

      <DateSelector
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
        cutoffRule={cutoffRule}
        onCutoffChange={setCutoffRule}
      />

      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '20px' }}>
        <MetricCard title="MAE" value={initialMetrics.mae_mw} unit="MW" description="Mean Absolute Error" />
        <MetricCard title="RMSE" value={initialMetrics.rmse_mw} unit="MW" description="Root Mean Squared Error" />
        <MetricCard title="Signed Bias" value={initialMetrics.bias_mw} unit="MW" description="Mean (Forecast - Actual)" />
        <MetricCard title="WAPE" value={initialMetrics.wape_percent} unit="%" description="Weighted Absolute Percentage Error" />
      </div>

      <CoverageSummary metrics={initialMetrics} />

      <ForecastChart data={[]} />

      <ForecastTable intervals={[]} />
    </div>
  );
};

export default App;
