import React from 'react';
import { DailyForecastPoint } from '../types/weather';

interface ForecastGridProps {
  daily: DailyForecastPoint[];
}

export const ForecastGrid: React.FC<ForecastGridProps> = ({ daily }) => {
  const getDayName = (dateStr: string, index: number) => {
    if (index === 0) return 'Today';
    if (index === 1) return 'Tomorrow';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
          7-Day Forecast & Trends
        </h3>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Ensemble Daily Projection
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '0.75rem'
      }}>
        {daily.slice(0, 7).map((day, idx) => (
          <div
            key={day.date}
            style={{
              background: idx === 0 ? 'rgba(56, 189, 248, 0.08)' : 'rgba(30, 41, 59, 0.4)',
              border: idx === 0 ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: '14px',
              padding: '1rem 0.75rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: '6px'
            }}
          >
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: idx === 0 ? '#38bdf8' : '#f8fafc' }}>
              {getDayName(day.date, idx)}
            </span>
            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
              {day.date.slice(5)}
            </span>
            
            <div style={{ fontSize: '2rem', margin: '4px 0' }}>
              {day.weather_icon}
            </div>

            <div style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 500 }}>
              {day.weather_condition}
            </div>

            {/* High / Low Temp */}
            <div style={{ display: 'flex', gap: '8px', alignItems: 'baseline', marginTop: '4px' }}>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc' }}>
                {Math.round(day.temperature_max_c)}°
              </span>
              <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                {Math.round(day.temperature_min_c)}°
              </span>
            </div>

            {/* Rain Chance */}
            {day.precipitation_probability_max_pct > 20 && (
              <span style={{
                fontSize: '0.7rem',
                color: '#38bdf8',
                background: 'rgba(56, 189, 248, 0.12)',
                padding: '2px 6px',
                borderRadius: '6px',
                marginTop: '4px'
              }}>
                🌧️ {day.precipitation_probability_max_pct}% ({day.precipitation_sum_mm}mm)
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
