import React, { useState, useMemo } from 'react';
import { IntervalDataPoint, DataStatus } from '../types';

interface ForecastTableProps {
  intervals: IntervalDataPoint[];
}

type SortField = 'period' | 'time' | 'actual' | 'forecast' | 'error';
type SortOrder = 'asc' | 'desc';

export const ForecastTable: React.FC<ForecastTableProps> = ({ intervals }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [sortField, setSortField] = useState<SortField>('period');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const filteredAndSorted = useMemo(() => {
    let result = [...intervals];

    if (filterStatus !== 'ALL') {
      result = result.filter((item) => item.status === filterStatus);
    }

    result.sort((a, b) => {
      let valA: any;
      let valB: any;

      switch (sortField) {
        case 'period':
          valA = a.settlement_period;
          valB = b.settlement_period;
          break;
        case 'time':
          valA = a.interval_start;
          valB = b.interval_start;
          break;
        case 'actual':
          valA = a.actual_mw ?? -999999;
          valB = b.actual_mw ?? -999999;
          break;
        case 'forecast':
          valA = a.forecast_mw ?? -999999;
          valB = b.forecast_mw ?? -999999;
          break;
        case 'error':
          valA = a.error_mw ?? -999999;
          valB = b.error_mw ?? -999999;
          break;
        default:
          valA = a.settlement_period;
          valB = b.settlement_period;
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [intervals, filterStatus, sortField, sortOrder]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getStatusBadge = (status: DataStatus) => {
    switch (status) {
      case 'MATCHED':
        return (
          <span style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>
            MATCHED
          </span>
        );
      case 'MISSING_FORECAST':
        return (
          <span style={{ backgroundColor: 'rgba(251, 191, 36, 0.15)', color: '#fbbf24', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>
            MISSING FC
          </span>
        );
      case 'MISSING_ACTUAL':
        return (
          <span style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#f87171', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>
            MISSING ACT
          </span>
        );
      case 'MISSING_BOTH':
        return (
          <span style={{ backgroundColor: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>
            MISSING BOTH
          </span>
        );
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '20px',
        marginBottom: '24px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
          Settlement Period Interval Details ({filteredAndSorted.length} Records)
        </h3>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <label style={{ fontSize: '12px', color: '#94a3b8' }}>Filter Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            <option value="ALL">All Intervals (48)</option>
            <option value="MATCHED">Matched Pairs Only</option>
            <option value="MISSING_FORECAST">Missing Forecast Only</option>
            <option value="MISSING_ACTUAL">Missing Actual Only</option>
          </select>
        </div>
      </div>

      <div style={{ maxHeight: '440px', overflowY: 'auto', border: '1px solid #334155', borderRadius: '6px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
          <thead style={{ position: 'sticky', top: 0, backgroundColor: '#0f172a', zIndex: 10 }}>
            <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
              <th onClick={() => toggleSort('period')} style={{ padding: '10px 12px', cursor: 'pointer' }}>
                Period {sortField === 'period' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
              </th>
              <th onClick={() => toggleSort('time')} style={{ padding: '10px 12px', cursor: 'pointer' }}>
                Delivery Time (UTC) {sortField === 'time' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
              </th>
              <th onClick={() => toggleSort('forecast')} style={{ padding: '10px 12px', cursor: 'pointer' }}>
                Forecast (MW) {sortField === 'forecast' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
              </th>
              <th style={{ padding: '10px 12px' }}>
                Publish Time (UTC)
              </th>
              <th onClick={() => toggleSort('actual')} style={{ padding: '10px 12px', cursor: 'pointer' }}>
                Actual (MW) {sortField === 'actual' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
              </th>
              <th onClick={() => toggleSort('error')} style={{ padding: '10px 12px', cursor: 'pointer' }}>
                Signed Error (MW) {sortField === 'error' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
              </th>
              <th style={{ padding: '10px 12px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
                  No intervals match the selected filter.
                </td>
              </tr>
            ) : (
              filteredAndSorted.map((item) => {
                const startTimeUTC = item.interval_start
                  ? new Date(item.interval_start).toISOString().replace('T', ' ').substring(0, 16)
                  : '-';
                const pubTimeUTC = item.publish_time
                  ? new Date(item.publish_time).toISOString().replace('T', ' ').substring(0, 16)
                  : '-';

                return (
                  <tr
                    key={item.settlement_period}
                    style={{
                      borderBottom: '1px solid #1e293b',
                      backgroundColor: item.status !== 'MATCHED' ? 'rgba(30, 41, 59, 0.4)' : undefined
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#f1f5f9' }}>
                      {item.settlement_period}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#cbd5e1', fontFamily: 'monospace' }}>
                      {startTimeUTC}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#38bdf8', fontWeight: 500, fontFamily: 'monospace' }}>
                      {item.forecast_mw !== null ? item.forecast_mw.toLocaleString() : '-'}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8', fontSize: '11px', fontFamily: 'monospace' }}>
                      {pubTimeUTC}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#34d399', fontWeight: 500, fontFamily: 'monospace' }}>
                      {item.actual_mw !== null ? item.actual_mw.toLocaleString() : '-'}
                    </td>
                    <td
                      style={{
                        padding: '10px 12px',
                        fontFamily: 'monospace',
                        fontWeight: 600,
                        color:
                          item.error_mw === null
                            ? '#64748b'
                            : item.error_mw > 0
                            ? '#fbbf24'
                            : item.error_mw < 0
                            ? '#60a5fa'
                            : '#cbd5e1'
                      }}
                    >
                      {item.error_mw !== null ? (item.error_mw > 0 ? `+${item.error_mw}` : item.error_mw) : '-'}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      {getStatusBadge(item.status)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
