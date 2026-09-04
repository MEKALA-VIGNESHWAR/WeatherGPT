import React from 'react';
import { CurrentWeather, TrustMetadata } from '../types/weather';
import { Wind, Droplets, CloudRain, Shield } from './Icons';

interface WeatherCardProps {
  weather: CurrentWeather;
  locationName: string;
  trust: TrustMetadata;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather, locationName, trust }) => {
  const getConfidenceBadgeColor = (conf: string) => {
    switch (conf.toLowerCase()) {
      case 'high': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'low': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '1.75rem', position: 'relative', overflow: 'hidden' }}>
      
      {/* Background Subtle Gradient Glow */}
      <div style={{
        position: 'absolute',
        top: '-40px',
        right: '-40px',
        width: '180px',
        height: '180px',
        background: 'radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%)',
        borderRadius: '50%',
        pointerEvents: 'none'
      }} />

      {/* Top Meta: Location & Trust Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.2rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#38bdf8', fontWeight: 700 }}>
            CURRENT CONDITIONS
          </span>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '2px', color: '#f8fafc' }}>
            {locationName}
          </h2>
        </div>

        {/* Trust & Authority Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(30, 41, 59, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '4px 10px',
          borderRadius: '9999px',
          fontSize: '0.75rem'
        }}>
          <Shield size={13} color="#38bdf8" />
          <span style={{ color: '#cbd5e1' }}>{trust.source}</span>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: getConfidenceBadgeColor(trust.confidence)
          }} />
          <span style={{ color: getConfidenceBadgeColor(trust.confidence), fontWeight: 600 }}>
            {trust.confidence.toUpperCase()} CONFIDENCE
          </span>
        </div>
      </div>

      {/* Hero Temperature & Condition */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '1.5rem 0' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
            <span style={{ fontSize: '4.2rem', fontWeight: 800, lineHeight: 1, letterSpacing: '-0.03em' }}>
              {Math.round(weather.temperature_c)}°
            </span>
            <span style={{ fontSize: '1.75rem', color: '#94a3b8', fontWeight: 600 }}>C</span>
          </div>
          <div style={{ fontSize: '0.95rem', color: '#94a3b8', marginTop: '6px' }}>
            Feels like <strong style={{ color: '#e2e8f0' }}>{Math.round(weather.feels_like_c)}°C</strong> • {weather.weather_condition}
          </div>
        </div>

        <div style={{ fontSize: '4.5rem', filter: 'drop-shadow(0 0 20px rgba(255,255,255,0.2))' }}>
          {weather.weather_icon}
        </div>
      </div>

      {/* 4 Metric Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
        gap: '0.75rem',
        paddingTop: '1.25rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        
        {/* Humidity */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#38bdf8', fontSize: '0.75rem' }}>
            <Droplets size={14} />
            <span>Humidity</span>
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>
            {weather.relative_humidity_pct}%
          </div>
        </div>

        {/* Wind */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#38bdf8', fontSize: '0.75rem' }}>
            <Wind size={14} />
            <span>Wind</span>
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>
            {Math.round(weather.wind_speed_kmh)} <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>km/h</span>
          </div>
        </div>

        {/* Rain Probability */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#38bdf8', fontSize: '0.75rem' }}>
            <CloudRain size={14} />
            <span>Rain Prob</span>
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>
            {weather.precipitation_probability_pct ?? 0}%
          </div>
        </div>

        {/* Pressure / UV */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '12px' }}>
          <div style={{ color: '#38bdf8', fontSize: '0.75rem' }}>
            Pressure / UV
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '4px' }}>
            {weather.surface_pressure_hpa ? `${Math.round(weather.surface_pressure_hpa)} hPa` : '1013 hPa'}
          </div>
        </div>

      </div>

      {/* Freshness Footer */}
      <div style={{
        marginTop: '1rem',
        fontSize: '0.72rem',
        color: '#64748b',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>Observed: {trust.data_age_minutes < 2 ? 'Just now' : `${trust.data_age_minutes}m ago`}</span>
        <span>Sunrise: {weather.sunrise || '06:00'} • Sunset: {weather.sunset || '18:30'}</span>
      </div>

    </div>
  );
};
