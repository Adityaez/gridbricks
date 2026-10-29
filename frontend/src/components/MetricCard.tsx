import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number | null;
  unit?: string;
  description?: string;
  color?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  description,
  color = '#0284c7'
}) => {
  return (
    <div style={{
      backgroundColor: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '8px',
      padding: '16px',
      minWidth: '160px',
      flex: 1
    }}>
      <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>{title}</div>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color: color }}>
        {value !== null && value !== undefined ? `${value}${unit ? ` ${unit}` : ''}` : 'N/A'}
      </div>
      {description && (
        <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>{description}</div>
      )}
    </div>
  );
};

