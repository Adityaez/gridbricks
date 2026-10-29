import React from 'react';
import { IntervalDataPoint } from '../types';

interface ForecastTableProps {
  intervals: IntervalDataPoint[];
}

export const ForecastTable: React.FC<ForecastTableProps> = ({ intervals }) => {
  return (
    <div style={{
      backgroundColor: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px'
    }}>
      <h3 style={{ margin: '0 0 15px 0', fontSize: '16px', color: '#f1f5f9' }}>
        Settlement Period Details (48 Half-Hours)
      </h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
              <th style={{ padding: '8px' }}>Period</th>
              <th style={{ padding: '8px' }}>Interval Start (UTC)</th>
              <th style={{ padding: '8px' }}>Forecast (MW)</th>
              <th style={{ padding: '8px' }}>Publish Time (UTC)</th>
              <th style={{ padding: '8px' }}>Actual (MW)</th>
              <th style={{ padding: '8px' }}>Signed Error (MW)</th>
              <th style={{ padding: '8px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {intervals.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
                  No intervals loaded.
                </td>
              </tr>
            ) : (
              intervals.map((item) => (
                <tr key={item.interval_start} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '8px' }}>{item.settlement_period}</td>
                  <td style={{ padding: '8px' }}>{item.interval_start}</td>
                  <td style={{ padding: '8px' }}>{item.forecast_mw ?? '-'}</td>
                  <td style={{ padding: '8px' }}>{item.publish_time ?? '-'}</td>
                  <td style={{ padding: '8px' }}>{item.actual_mw ?? '-'}</td>
                  <td style={{ padding: '8px' }}>{item.error_mw ?? '-'}</td>
                  <td style={{ padding: '8px' }}>{item.status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

