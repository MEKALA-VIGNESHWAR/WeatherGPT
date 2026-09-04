import React from 'react';
import { HourlyForecastPoint } from '../types/weather';

interface HourlySliderProps {
  hourly: HourlyForecastPoint[];
}

export const HourlySlider: React.FC<HourlySliderProps> = ({ hourly }) => {
  return (
    <div className="glass-panel" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
          24-Hour Timeline Forecast
        </h3>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Hourly NWP Resolution
        </span>
      </div>

      <div style={{
        display: 'flex',
        gap: '0.85rem',
        overflowX: 'auto',
        paddingBottom: '0.5rem'
      }}>
        {hourly.slice(0, 24).map((pt, i) => {
          const hourLabel = pt.time.includes('T') ? pt.time.split('T')[1].slice(0, 5) : pt.time;
          return (
            <div
              key={i}
              style={{
                flex: '0 0 auto',
                width: '78px',
                background: 'rgba(30, 41, 59, 0.4)',
                borderRadius: '12px',
                padding: '0.75rem 0.5rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                border: '1px solid rgba(255, 255, 255, 0.05)'
              }}
            >
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 500 }}>
                {i === 0 ? 'Now' : hourLabel}
              </span>
              <span style={{ fontSize: '1.5rem', margin: '2px 0' }}>
                {pt.weather_icon}
              </span>
              <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                {Math.round(pt.temperature_c)}°
              </span>
              
              {/* Rain prob pill */}
              {pt.precipitation_probability_pct > 0 ? (
                <span style={{
                  fontSize: '0.65rem',
                  padding: '1px 5px',
                  borderRadius: '9999px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: '#38bdf8',
                  fontWeight: 600
                }}>
                  {pt.precipitation_probability_pct}%
                </span>
              ) : (
                <span style={{ fontSize: '0.65rem', color: '#64748b' }}>0%</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
