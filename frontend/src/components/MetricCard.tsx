import React, { useState } from 'react';

interface MetricCardProps {
  title: string;
  value: string | number | null;
  unit?: string;
  description?: string;
  formula?: string;
  color?: string;
  badge?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  description,
  formula,
  color = '#38bdf8',
  badge
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '16px 20px',
        minWidth: '180px',
        flex: 1,
        position: 'relative',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '13px', fontWeight: 500, color: '#94a3b8', letterSpacing: '0.02em' }}>
          {title}
        </span>
        {formula && (
          <button
            type="button"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            onClick={() => setShowTooltip(!showTooltip)}
            aria-label={`Formula for ${title}`}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748b',
              cursor: 'pointer',
              fontSize: '12px',
              padding: '0 4px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ⓘ
          </button>
        )}
      </div>

      {showTooltip && formula && (
        <div
          style={{
            position: 'absolute',
            top: '36px',
            right: '12px',
            backgroundColor: '#0f172a',
            border: '1px solid #475569',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '11px',
            color: '#e2e8f0',
            zIndex: 30,
            maxWidth: '220px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.4)'
          }}
        >
          {formula}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span style={{ fontSize: '26px', fontWeight: 700, color: color, fontFamily: 'monospace' }}>
          {value !== null && value !== undefined ? value : 'N/A'}
        </span>
        {unit && value !== null && value !== undefined && (
          <span style={{ fontSize: '14px', color: '#94a3b8', fontWeight: 500 }}>{unit}</span>
        )}
        {badge && (
          <span
            style={{
              marginLeft: 'auto',
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: '#334155',
              color: '#cbd5e1'
            }}
          >
            {badge}
          </span>
        )}
      </div>

      {description && (
        <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
          {description}
        </div>
      )}
    </div>
  );
};
