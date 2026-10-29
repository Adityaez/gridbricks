import React from 'react';
import { IntervalDataPoint } from '../types';

interface ForecastChartProps {
  data: IntervalDataPoint[];
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ data }) => {
  return (
    <div style={{
      backgroundColor: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px'
    }}>
      <h3 style={{ margin: '0 0 15px 0', fontSize: '16px', color: '#f1f5f9' }}>
        Forecast vs. Actual Wind Generation (30-min Intervals)
      </h3>
      {data.length === 0 ? (
        <div style={{ color: '#94a3b8', padding: '40px 0', textAlign: 'center' }}>
          No interval data available for the selected parameters.
        </div>
      ) : (
        <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
          Chart visualization placeholder (Recharts will render actual vs forecast series)
        </div>
      )}
    </div>
  );
};
