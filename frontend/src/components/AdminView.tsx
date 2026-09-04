import React, { useEffect, useState } from 'react';
import { fetchAdminMetrics } from '../services/api';
import { Activity, Shield, AlertTriangle, RefreshCw } from './Icons';

export const AdminView: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await fetchAdminMetrics();
      setMetrics(data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  if (loading || !metrics) {
    return (
      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#38bdf8' }}>
        ⚡ Querying telemetry and weather provider health checks...
      </div>
    );
  }

  const m = metrics.metrics;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="#10b981" />
            WeatherGPT System Operations & Observability
          </h3>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
            Environment: <strong>{metrics.environment.toUpperCase()}</strong> • Platform Version: {metrics.version}
          </div>
        </div>

        <button
          onClick={loadMetrics}
          style={{
            background: 'rgba(30, 41, 59, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '0.4rem 0.8rem',
            borderRadius: '8px',
            color: '#38bdf8',
            fontSize: '0.8rem',
            cursor: 'pointer'
          }}
        >
          🔄 Refresh Metrics
        </button>
      </div>

      {/* 4 Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>System Status</span>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
            {metrics.system_status}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '4px' }}>
            All microservices healthy
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Queries Processed</span>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
            {m.total_queries_processed}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#10b981', marginTop: '4px' }}>
            Avg Latency: {m.average_api_latency_ms} ms
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>User Satisfaction</span>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
            {m.satisfaction_rate_pct}%
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '4px' }}>
            {m.total_feedbacks} verified ratings
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Cache Hit Ratio</span>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#a855f7', marginTop: '4px' }}>
            {m.cache_hit_rate_pct}%
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '4px' }}>
            In-Memory & Redis Layer
          </div>
        </div>

      </div>

      {/* Sources Health Table */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', marginBottom: '1rem' }}>
          Integrated Meteorological Providers & Models
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {metrics.sources_health.map((s: any, idx: number) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem 1rem',
                background: 'rgba(30, 41, 59, 0.4)',
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                fontSize: '0.85rem'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Shield size={16} color="#38bdf8" />
                <span style={{ fontWeight: 600, color: '#f8fafc' }}>{s.source}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>
                  Sync: {s.last_ingest}
                </span>
                <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>
                  {s.latency_ms > 0 ? `${s.latency_ms} ms` : 'Grid Ready'}
                </span>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: s.status === 'HEALTHY' || s.status === 'ONLINE' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                  color: s.status === 'HEALTHY' || s.status === 'ONLINE' ? '#10b981' : '#f59e0b'
                }}>
                  {s.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
