import React, { useState, useEffect } from 'react';
import { fetchSectorAdvisories } from '../services/api';
import { SectorAdvisoryResponse } from '../types/advisory';
import { Tractor, Shield, AlertTriangle, CloudRain, Wind } from './Icons';

interface SectorAdvisoryViewProps {
  latitude: number;
  longitude: number;
  locationName: string;
}

export const SectorAdvisoryView: React.FC<SectorAdvisoryViewProps> = ({
  latitude,
  longitude,
  locationName
}) => {
  const [activeSector, setActiveSector] = useState<'agriculture' | 'disaster' | 'citizen' | 'marine' | 'aviation'>('agriculture');
  const [selectedCrop, setSelectedCrop] = useState('paddy');
  const [advisoryData, setAdvisoryData] = useState<SectorAdvisoryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAdvisory();
  }, [activeSector, selectedCrop, latitude, longitude]);

  const loadAdvisory = async () => {
    setLoading(true);
    try {
      const data = await fetchSectorAdvisories(activeSector, latitude, longitude, selectedCrop);
      setAdvisoryData(data);
    } catch {
      // Fallback handled gracefully
    } finally {
      setLoading(false);
    }
  };

  const crops = [
    { id: 'paddy', name: '🌾 Paddy (Rice)' },
    { id: 'cotton', name: '🌱 Cotton' },
    { id: 'wheat', name: '🌾 Wheat' },
    { id: 'sugarcane', name: '🎋 Sugarcane' },
    { id: 'chilli', name: '🌶️ Chilli / Spices' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Sector Tabs */}
      <div className="glass-panel" style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {[
            { id: 'agriculture', label: '🌾 Agriculture', desc: 'Irrigation & Spraying' },
            { id: 'disaster', label: '🚨 Disaster Response', desc: 'Flood & Cyclone SOPs' },
            { id: 'citizen', label: '🚗 Citizen & Commute', desc: 'Roads & Daily Life' },
            { id: 'marine', label: '🌊 Marine / Fishermen', desc: 'Coastal Sea State' },
            { id: 'aviation', label: '✈️ Aviation / Drone', desc: 'Flight Constraints' }
          ].map((sec) => (
            <button
              key={sec.id}
              onClick={() => setActiveSector(sec.id as any)}
              style={{
                padding: '0.6rem 1rem',
                borderRadius: '10px',
                border: 'none',
                background: activeSector === sec.id ? '#0284c7' : 'rgba(30, 41, 59, 0.6)',
                color: activeSector === sec.id ? '#fff' : '#cbd5e1',
                fontWeight: activeSector === sec.id ? 700 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              {sec.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: '8px',
            padding: '0.35rem 0.75rem',
            fontSize: '0.8rem',
            color: '#38bdf8',
            fontWeight: 600
          }}>
            <span>📍</span>
            <span>{locationName}</span>
          </div>

          {activeSector === 'agriculture' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Crop:</span>
              <select
                value={selectedCrop}
                onChange={(e) => setSelectedCrop(e.target.value)}
                style={{
                  background: '#1e293b',
                  color: '#f8fafc',
                  border: '1px solid rgba(255,255,255,0.1)',
                  padding: '0.4rem 0.8rem',
                  borderRadius: '8px',
                  fontSize: '0.82rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                {crops.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Advisory Content Cards */}
      {loading ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#38bdf8' }}>
          ⚡ Evaluating domain agronomic & risk thresholds...
        </div>
      ) : advisoryData ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {advisoryData.recommendations.map((rec, i) => {
            const isCaution = rec.verdict.includes('DELAY') || rec.verdict.includes('CAUTION') || rec.verdict.includes('NOT_RECOMMENDED');
            const isDanger = rec.verdict.includes('HAZARD') || rec.verdict.includes('DANGER');
            const badgeColor = isDanger ? '#ef4444' : isCaution ? '#f59e0b' : '#10b981';

            return (
              <div
                key={i}
                className="glass-panel"
                style={{
                  padding: '1.5rem',
                  borderTop: `4px solid ${badgeColor}`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1.6rem' }}>{rec.icon}</span>
                      <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc' }}>
                        {rec.title}
                      </h4>
                    </div>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '6px',
                      background: `${badgeColor}22`,
                      color: badgeColor,
                      border: `1px solid ${badgeColor}44`
                    }}>
                      {rec.verdict.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.92rem', color: '#e2e8f0', lineHeight: 1.5, marginBottom: '1rem' }}>
                    {rec.summary}
                  </p>

                  {/* Meteorological Reasons */}
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                      Weather Trigger & Basis:
                    </div>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.82rem', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {rec.reasons.map((r, ri) => (
                        <li key={ri}>{r}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Actionable Steps */}
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '0.75rem', borderRadius: '10px' }}>
                    <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                      Recommended Action:
                    </div>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.82rem', color: '#e2e8f0', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {rec.actionable_steps.map((s, si) => (
                        <li key={si}>{s}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '0.72rem', color: '#64748b', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Valid Until: {rec.valid_until}</span>
                  <span>Authority: {advisoryData.source}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

    </div>
  );
};
