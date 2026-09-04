import React from 'react';
import { WeatherAlert } from '../types/alert';
import { AlertTriangle, Shield } from './Icons';

interface AlertBannerProps {
  alerts: WeatherAlert[];
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alerts }) => {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
      {alerts.map((alert) => {
        const isRed = alert.severity === 'red';
        const isOrange = alert.severity === 'orange';
        const bg = isRed
          ? 'rgba(239, 68, 68, 0.12)'
          : isOrange
          ? 'rgba(249, 115, 22, 0.12)'
          : 'rgba(245, 158, 11, 0.12)';
        const border = isRed ? '#ef4444' : isOrange ? '#f97316' : '#f59e0b';
        const textColor = isRed ? '#fca5a5' : isOrange ? '#fdba74' : '#fde047';

        return (
          <div
            key={alert.id}
            className="glass-panel"
            style={{
              background: bg,
              borderColor: border,
              borderLeftWidth: '5px',
              padding: '1.25rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '1rem'
            }}
          >
            <div style={{
              background: border,
              borderRadius: '50%',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#000',
              flexShrink: 0
            }}>
              <AlertTriangle size={20} color="#000" />
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '4px' }}>
                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: border,
                  color: '#000'
                }}>
                  {alert.severity.toUpperCase()} ALERT
                </span>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  {alert.area_desc} • {alert.source}
                </span>
              </div>

              <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', marginBottom: '4px' }}>
                {alert.headline}
              </h4>

              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.4, marginBottom: '8px' }}>
                {alert.description}
              </p>

              <div style={{
                background: 'rgba(0, 0, 0, 0.25)',
                padding: '0.6rem 0.8rem',
                borderRadius: '8px',
                fontSize: '0.82rem',
                color: textColor,
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <Shield size={14} color={border} />
                <span><strong>Actionable Instruction:</strong> {alert.instruction}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
