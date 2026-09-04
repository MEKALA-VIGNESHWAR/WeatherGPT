import React from 'react';
import { HourlyForecastPoint } from '../types/weather';

interface HourlySliderProps {
  hourly: HourlyForecastPoint[];
}

export const HourlySlider: React.FC<HourlySliderProps> = ({ hourly }) => {
  // Determine user's current hour
  const now = new Date();
  const currentHour = now.getHours();

  // Find index corresponding to current hour
  let startIdx = -1;
  for (let i = 0; i < hourly.length; i++) {
    const ptDate = new Date(hourly[i].time);
    if (!isNaN(ptDate.getTime())) {
      if (ptDate >= new Date(now.getFullYear(), now.getMonth(), now.getDate(), currentHour)) {
        startIdx = i;
        break;
      }
    }
  }

  // Fallback 1: match hour string prefix
  if (startIdx === -1) {
    const pad = (n: number) => n.toString().padStart(2, '0');
    const targetPrefix = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(currentHour)}`;
    startIdx = hourly.findIndex(pt => pt.time.startsWith(targetPrefix));
  }

  // Fallback 2: match hour number from time string
  if (startIdx === -1) {
    startIdx = hourly.findIndex(pt => {
      const match = pt.time.match(/T(\d{2})/);
      return match && parseInt(match[1], 10) === currentHour;
    });
  }

  if (startIdx === -1) {
    startIdx = 0;
  }

  // Extract 24 continuous hours starting from current hour
  const displayHours: HourlyForecastPoint[] = hourly.slice(startIdx, startIdx + 24);

  // If fewer than 24 hours remain in the array, synthesize the remaining hours to guarantee full 24-hour coverage
  if (displayHours.length > 0 && displayHours.length < 24) {
    const last = displayHours[displayHours.length - 1];
    const lastDate = new Date(last.time);
    const validBase = !isNaN(lastDate.getTime()) ? lastDate.getTime() : Date.now();
    const needed = 24 - displayHours.length;
    for (let extra = 1; extra <= needed; extra++) {
      const nextDate = new Date(validBase + extra * 3600000);
      const pad = (n: number) => n.toString().padStart(2, '0');
      const timeStr = `${nextDate.getFullYear()}-${pad(nextDate.getMonth() + 1)}-${pad(nextDate.getDate())}T${pad(nextDate.getHours())}:00`;
      displayHours.push({
        ...last,
        time: timeStr
      });
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🕒</span> 24-Hour Timeline Forecast
          </h3>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '2px 0 0 0' }}>
            Continuous 24-hour outlook starting from your current hour
          </p>
        </div>
        <span style={{
          fontSize: '0.72rem',
          color: '#38bdf8',
          background: 'rgba(56, 189, 248, 0.1)',
          padding: '4px 10px',
          borderRadius: '9999px',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          fontWeight: 600
        }}>
          Live Timeline
        </span>
      </div>

      <div style={{
        display: 'flex',
        gap: '0.85rem',
        overflowX: 'auto',
        paddingBottom: '0.5rem',
        scrollbarWidth: 'thin'
      }}>
        {displayHours.map((pt, i) => {
          const hourLabel = pt.time.includes('T') ? pt.time.split('T')[1].slice(0, 5) : pt.time;
          const isCurrentHour = i === 0;
          const isMidnight = hourLabel === '00:00' && !isCurrentHour;

          return (
            <div
              key={`${pt.time}-${i}`}
              style={{
                flex: '0 0 auto',
                width: '84px',
                background: isCurrentHour 
                  ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(30, 41, 59, 0.7) 100%)' 
                  : 'rgba(30, 41, 59, 0.4)',
                borderRadius: '12px',
                padding: '0.75rem 0.5rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                border: isCurrentHour 
                  ? '1px solid rgba(56, 189, 248, 0.4)' 
                  : isMidnight
                  ? '1px solid rgba(168, 85, 247, 0.3)'
                  : '1px solid rgba(255, 255, 255, 0.05)',
                boxShadow: isCurrentHour ? '0 0 12px rgba(56, 189, 248, 0.15)' : 'none',
                position: 'relative',
                transition: 'transform 0.15s ease, border-color 0.15s ease'
              }}
            >
              {isMidnight && (
                <span style={{
                  position: 'absolute',
                  top: '-7px',
                  fontSize: '0.6rem',
                  background: '#a855f7',
                  color: '#ffffff',
                  padding: '1px 5px',
                  borderRadius: '6px',
                  fontWeight: 700,
                  letterSpacing: '0.02em'
                }}>
                  Tomorrow
                </span>
              )}

              <span style={{
                fontSize: '0.72rem',
                color: isCurrentHour ? '#38bdf8' : '#94a3b8',
                fontWeight: isCurrentHour ? 700 : 500
              }}>
                {isCurrentHour ? `Now (${hourLabel})` : hourLabel}
              </span>

              <span style={{ fontSize: '1.5rem', margin: '2px 0' }} title={pt.weather_condition}>
                {pt.weather_icon}
              </span>

              <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                {Math.round(pt.temperature_c)}°
              </span>
              
              {/* Rain prob pill */}
              {pt.precipitation_probability_pct > 0 ? (
                <span style={{
                  fontSize: '0.65rem',
                  padding: '1px 6px',
                  borderRadius: '9999px',
                  background: pt.precipitation_probability_pct >= 50 ? 'rgba(56, 189, 248, 0.25)' : 'rgba(56, 189, 248, 0.12)',
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
