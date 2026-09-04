import React, { useEffect, useState } from 'react';
import { fetchClimateTrends } from '../services/api';
import { CloudRain, Sun, Activity, Shield } from './Icons';

interface ClimateTrendsViewProps {
  latitude: number;
  longitude: number;
  locationName: string;
}

export const ClimateTrendsView: React.FC<ClimateTrendsViewProps> = ({
  latitude,
  longitude,
  locationName
}) => {
  const [trendData, setTrendData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrends();
  }, [latitude, longitude]);

  const loadTrends = async () => {
    setLoading(true);
    try {
      const data = await fetchClimateTrends(latitude, longitude, '7_days');
      setTrendData(data);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  if (loading || !trendData) {
    return (
      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#38bdf8' }}>
        ⚡ Loading historical observation records and climatological baselines...
      </div>
    );
  }

  const dates: string[] = trendData.dates || [];
  const rainValues: number[] = trendData.precipitation_mm || [];
  const maxTemps: number[] = trendData.max_temperature_c || [];
  const maxRain = Math.max(...rainValues, 10);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontSize: '0.8rem' }}>
            <CloudRain size={16} />
            <span>7-Day Total Precipitation</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '6px' }}>
            {trendData.total_precipitation_mm} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>mm</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '4px' }}>
            Status: {trendData.anomaly_analysis?.rainfall_status || 'Normal Seasonal'}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b', fontSize: '0.8rem' }}>
            <Sun size={16} />
            <span>Average Maximum Temperature</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '6px' }}>
            {trendData.average_max_temp_c}° <span style={{ fontSize: '1rem', color: '#94a3b8' }}>C</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>
            Departure: {trendData.anomaly_analysis?.temperature_anomaly_c > 0 ? `+${trendData.anomaly_analysis.temperature_anomaly_c}°C` : `${trendData.anomaly_analysis.temperature_anomaly_c}°C`} vs Norm
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontSize: '0.8rem' }}>
            <Shield size={16} />
            <span>Data Provenance</span>
          </div>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            IMD / ECMWF Reanalysis
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '6px' }}>
            {trendData.confidence}
          </div>
        </div>

      </div>

      {/* Rainfall Trend Bar Chart */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc' }}>
              Observed Daily Rainfall (Past 7 Days)
            </h3>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Station / Grid Catchment Totals in Millimeters (mm)
            </div>
          </div>
          <span style={{ fontSize: '0.75rem', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '3px 8px', borderRadius: '6px' }}>
            {locationName}
          </span>
        </div>

        {/* Visual Bar Graph */}
        <div style={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          height: '200px',
          padding: '1rem 0',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          {dates.map((dateStr, idx) => {
            const val = rainValues[idx] || 0;
            const heightPct = Math.max(8, (val / maxRain) * 100);

            return (
              <div
                key={dateStr}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px',
                  flex: 1,
                  height: '100%',
                  justifyContent: 'flex-end'
                }}
              >
                <span style={{ fontSize: '0.75rem', color: val > 0 ? '#38bdf8' : '#64748b', fontWeight: 700 }}>
                  {val.toFixed(1)}
                </span>
                <div style={{
                  width: '32px',
                  height: `${heightPct}%`,
                  background: val > 15 ? 'linear-gradient(180deg, #38bdf8 0%, #0284c7 100%)' : 'rgba(56, 189, 248, 0.35)',
                  borderRadius: '6px 6px 0 0',
                  transition: 'height 0.5s ease',
                  border: '1px solid rgba(56, 189, 248, 0.5)'
                }} />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  {dateStr.slice(5)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};
