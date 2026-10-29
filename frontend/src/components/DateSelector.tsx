import React from 'react';

interface DateSelectorProps {
  selectedDate: string;
  onDateChange: (newDate: string) => void;
  cutoffRule: string;
  onCutoffChange: (rule: string) => void;
}

export const DateSelector: React.FC<DateSelectorProps> = ({
  selectedDate,
  onDateChange,
  cutoffRule,
  onCutoffChange
}) => {
  return (
    <div style={{
      display: 'flex',
      gap: '20px',
      alignItems: 'center',
      padding: '16px 20px',
      backgroundColor: '#1e293b',
      borderRadius: '8px',
      border: '1px solid #334155',
      marginBottom: '20px',
      flexWrap: 'wrap'
    }}>
      <div>
        <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
          Delivery Date (Jan 2026 Only)
        </label>
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
            padding: '8px 12px',
            fontSize: '14px'
          }}
        />
      </div>

      <div>
        <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
          Decision Cutoff Strategy
        </label>
        <select
          value={cutoffRule}
          onChange={(e) => onCutoffChange(e.target.value)}
          style={{
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            border: '1px solid #475569',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '14px'
          }}
        >
          <option value="day_ahead_1700">Day-Ahead 17:00 UTC (D-1)</option>
          <option value="gate_closure">Gate Closure (T - 1 hour)</option>
          <option value="fixed_4h">Fixed 4-Hour Lead Time</option>
        </select>
      </div>

      <div style={{ marginLeft: 'auto', fontSize: '12px', color: '#94a3b8' }}>
        <span>Scope: <strong>Elexon FUELHH & WINDFOR</strong></span>
      </div>
    </div>
  );
};

