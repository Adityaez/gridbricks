import React, { useState, useEffect, useCallback } from 'react';
import { DateSelector, ViewMode } from './components/DateSelector';
import { MetricCard } from './components/MetricCard';
import { ForecastChart } from './components/ForecastChart';
import { ForecastTable } from './components/ForecastTable';
import { CoverageSummary } from './components/CoverageSummary';
import { ForecastEvolutionChart } from './components/ForecastEvolutionChart';
import { RangeAnalyticsView } from './components/RangeAnalyticsView';
import { fetchDashboard } from './services/api';
import { DashboardResponse } from './types';

export const App: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('2026-01-15');
  const [cutoffRule, setCutoffRule] = useState<string>('day_ahead_1700');
  const [hourlyExpansion, setHourlyExpansion] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');

  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard(selectedDate, cutoffRule, hourlyExpansion);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to WindSight backend API.');
    } finally {
      setLoading(false);
    }
  }, [selectedDate, cutoffRule, hourlyExpansion]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '28px 24px', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* App Header */}
      <header style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '24px' }}>💨</span>
              <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                WindSight
              </h1>
              <span style={{ color: '#64748b', fontSize: '20px' }}>/</span>
              <span style={{ fontSize: '15px', color: '#94a3b8', fontWeight: 500 }}>
                Day-Ahead Wind Forecast Intelligence
              </span>
            </div>
            <p style={{ margin: '6px 0 0 0', fontSize: '13px', color: '#64748b' }}>
              Procurement desk evaluation of UK national wind forecast accuracy against realized Elexon settlement actuals.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span
              style={{
                backgroundColor: 'rgba(2, 132, 199, 0.2)',
                color: '#38bdf8',
                border: '1px solid rgba(2, 132, 199, 0.4)',
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '12px',
                fontWeight: 600
              }}
            >
              January 2026 Historical Pilot
            </span>
            <span
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                color: '#34d399',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '12px',
                fontWeight: 600
              }}
            >
              Zero Look-Ahead Bias
            </span>
          </div>
        </div>
      </header>

      {/* Date & Mode Navigation */}
      <DateSelector
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
        cutoffRule={cutoffRule}
        onCutoffChange={setCutoffRule}
        hourlyExpansion={hourlyExpansion}
        onHourlyExpansionChange={setHourlyExpansion}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Error Banner */}
      {error && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            borderRadius: '8px',
            padding: '16px 20px',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            color: '#fca5a5',
            fontSize: '13px'
          }}
        >
          <div>
            <strong>Error:</strong> {error}
          </div>
          <button
            type="button"
            onClick={loadData}
            style={{
              backgroundColor: '#ef4444',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              padding: '6px 12px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Content Sections Based on View Mode */}
      {viewMode === 'evolution' ? (
        <ForecastEvolutionChart date={selectedDate} cutoffRule={cutoffRule} />
      ) : viewMode === 'analytics' ? (
        <RangeAnalyticsView cutoffRule={cutoffRule} hourlyExpansion={hourlyExpansion} />
      ) : loading ? (
        <div style={{ padding: '80px 20px', textAlign: 'center', color: '#38bdf8' }}>
          <div style={{ fontSize: '28px', marginBottom: '12px' }}>⏳</div>
          <div style={{ fontSize: '15px', fontWeight: 500 }}>Loading decision-time forecasts &amp; realized actuals...</div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
            Fetching from Elexon BMRS FUELHH &amp; WINDFOR datasets
          </div>
        </div>
      ) : dashboardData ? (
        <>
          {/* Executive KPI Cards Strip */}
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' }}>
            <MetricCard
              title="MAE (Mean Absolute Error)"
              value={dashboardData.metrics.mae_mw}
              unit="MW"
              description="Average magnitude of forecast error"
              formula="MAE = (1/N) * Σ |Forecast - Actual|"
              color="#38bdf8"
            />
            <MetricCard
              title="RMSE (Root Mean Squared Error)"
              value={dashboardData.metrics.rmse_mw}
              unit="MW"
              description="Heavily penalizes large forecast misses"
              formula="RMSE = sqrt((1/N) * Σ (Forecast - Actual)^2)"
              color="#818cf8"
            />
            <MetricCard
              title="Signed Bias"
              value={dashboardData.metrics.bias_mw}
              unit="MW"
              description="Over-forecast (>0) or Under-forecast (<0)"
              formula="Bias = (1/N) * Σ (Forecast - Actual)"
              color={
                dashboardData.metrics.bias_mw === null
                  ? '#cbd5e1'
                  : dashboardData.metrics.bias_mw > 0
                  ? '#fbbf24'
                  : '#38bdf8'
              }
              badge={
                dashboardData.metrics.bias_mw !== null
                  ? dashboardData.metrics.bias_mw > 0
                    ? 'Over-Forecast'
                    : 'Under-Forecast'
                  : undefined
              }
            />
            <MetricCard
              title="WAPE"
              value={dashboardData.metrics.wape_percent}
              unit="%"
              description="Weighted Absolute Percentage Error"
              formula="WAPE = (Σ |Forecast - Actual| / Σ Actual) * 100%"
              color="#34d399"
            />
          </div>

          {/* Data Coverage Summary */}
          <CoverageSummary metrics={dashboardData.metrics} hourlyExpansion={hourlyExpansion} />

          {/* Forecast vs. Actual Visual Chart */}
          <ForecastChart data={dashboardData.intervals} />

          {/* Settlement Interval Details Table */}
          <ForecastTable intervals={dashboardData.intervals} />
        </>
      ) : null}

      {/* App Footer */}
      <footer style={{ marginTop: 'auto', paddingTop: '32px', borderTop: '1px solid #334155', color: '#64748b', fontSize: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <span>Data Sources: </span>
            <strong style={{ color: '#94a3b8' }}>Elexon BMRS FUELHH (WIND)</strong> &amp;{' '}
            <strong style={{ color: '#94a3b8' }}>WINDFOR Stream</strong> | Units: <strong>MW</strong> | Timezone: <strong>UTC</strong>
          </div>
          <div>
            <span>WindSight Pilot Assignment &bull; UK Electricity Procurement Desk</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
