import React from 'react';

export type ViewMode = 'dashboard' | 'evolution' | 'analytics';

interface DateSelectorProps {
  selectedDate: string;
  onDateChange: (newDate: string) => void;
  cutoffRule: string;
  onCutoffChange: (rule: string) => void;
  hourlyExpansion: boolean;
  onHourlyExpansionChange: (expanded: boolean) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

export const DateSelector: React.FC<DateSelectorProps> = ({
  selectedDate,
  onDateChange,
  cutoffRule,
  onCutoffChange,
  hourlyExpansion,
  onHourlyExpansionChange,
  viewMode,
  onViewModeChange
}) => {
  // Navigation helpers
  const handlePrevDay = () => {
    const current = new Date(selectedDate);
    current.setUTCDate(current.getUTCDate() - 1);
    const prevStr = current.toISOString().slice(0, 10);
    if (prevStr >= '2026-01-01') {
      onDateChange(prevStr);
    }
  };

  const handleNextDay = () => {
    const current = new Date(selectedDate);
    current.setUTCDate(current.getUTCDate() + 1);
    const nextStr = current.toISOString().slice(0, 10);
    if (nextStr <= '2026-01-31') {
      onDateChange(nextStr);
    }
  };

  const isFirstDay = selectedDate <= '2026-01-01';
  const isLastDay = selectedDate >= '2026-01-31';

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
      {/* Top Bar: View Mode Switcher */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #334155', paddingBottom: '12px' }}>
        <button
          type="button"
          onClick={() => onViewModeChange('dashboard')}
          style={{
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            backgroundColor: viewMode === 'dashboard' ? '#0284c7' : '#0f172a',
            color: viewMode === 'dashboard' ? '#ffffff' : '#94a3b8',
            transition: 'all 0.2s'
          }}
        >
          Daily Dashboard
        </button>
        <button
          type="button"
          onClick={() => onViewModeChange('evolution')}
          style={{
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            backgroundColor: viewMode === 'evolution' ? '#0284c7' : '#0f172a',
            color: viewMode === 'evolution' ? '#ffffff' : '#94a3b8',
            transition: 'all 0.2s'
          }}
        >
          Forecast Evolution
        </button>
        <button
          type="button"
          onClick={() => onViewModeChange('analytics')}
          style={{
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            backgroundColor: viewMode === 'analytics' ? '#0284c7' : '#0f172a',
            color: viewMode === 'analytics' ? '#ffffff' : '#94a3b8',
            transition: 'all 0.2s'
          }}
        >
          Range Analytics (Jan 2026)
        </button>
      </div>

      {/* Controls Row */}
      <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
        {/* Date Selector with Prev / Next */}
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
            Delivery Date (Jan 2026)
          </label>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <button
              type="button"
              disabled={isFirstDay}
              onClick={handlePrevDay}
              style={{
                backgroundColor: '#0f172a',
                color: isFirstDay ? '#475569' : '#e2e8f0',
                border: '1px solid #475569',
                borderRadius: '4px',
                padding: '7px 10px',
                cursor: isFirstDay ? 'not-allowed' : 'pointer',
                fontSize: '12px',
                fontWeight: 'bold'
              }}
              title="Previous Day"
            >
              ◀
            </button>
            <input
              type="date"
              min="2026-01-01"
              max="2026-01-31"
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              style={{
                backgroundColor: '#0f172a',
                color: '#f8fafc',
                border: '1px solid #475569',
                borderRadius: '4px',
                padding: '6px 10px',
                fontSize: '13px'
              }}
            />
            <button
              type="button"
              disabled={isLastDay}
              onClick={handleNextDay}
              style={{
                backgroundColor: '#0f172a',
                color: isLastDay ? '#475569' : '#e2e8f0',
                border: '1px solid #475569',
                borderRadius: '4px',
                padding: '7px 10px',
                cursor: isLastDay ? 'not-allowed' : 'pointer',
                fontSize: '12px',
                fontWeight: 'bold'
              }}
              title="Next Day"
            >
              ▶
            </button>
          </div>
        </div>

        {/* Cutoff Strategy Selector */}
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
            Decision Cutoff Rule
          </label>
          <select
            value={cutoffRule}
            onChange={(e) => onCutoffChange(e.target.value)}
            style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '4px',
              padding: '7px 10px',
              fontSize: '13px'
            }}
          >
            <option value="day_ahead_1700">Day-Ahead 17:00 UTC (D-1)</option>
            <option value="gate_closure">Gate Closure (T - 1 hour)</option>
            <option value="fixed_4h">Fixed Lead Time (T - 4 hours)</option>
          </select>
        </div>

        {/* Hourly Expansion Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '18px' }}>
          <input
            type="checkbox"
            id="hourly-expansion"
            checked={hourlyExpansion}
            onChange={(e) => onHourlyExpansionChange(e.target.checked)}
            style={{ cursor: 'pointer', width: '16px', height: '16px' }}
          />
          <label
            htmlFor="hourly-expansion"
            style={{ fontSize: '13px', color: '#cbd5e1', cursor: 'pointer' }}
            title="WINDFOR forecasts are published hourly. Enabling this pairs the forecast with both half-hours of that delivery hour."
          >
            Expand hourly forecast to 30-min settlement intervals
          </label>
        </div>
      </div>
    </div>
  );
};
