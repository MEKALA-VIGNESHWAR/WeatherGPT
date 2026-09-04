import React, { useState, useEffect } from 'react';
import { fetchSectorAdvisories } from '../services/api';
import { SectorAdvisoryResponse, AdvisoryRecommendation } from '../types/advisory';

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
  const [horizonDays, setHorizonDays] = useState<number>(1);
  const [advisoryData, setAdvisoryData] = useState<SectorAdvisoryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAdvisory();
  }, [activeSector, selectedCrop, horizonDays, latitude, longitude]);

  const loadAdvisory = async () => {
    setLoading(true);
    try {
      const data = await fetchSectorAdvisories(activeSector, latitude, longitude, selectedCrop, horizonDays);
      setAdvisoryData(data);
    } catch {
      // Handled gracefully
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

  const getVerdictStyle = (verdict: string) => {
    const v = verdict.toUpperCase();
    if (v.includes('CRITICAL') || v.includes('HAZARD') || v.includes('DANGER')) {
      return { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)' };
    }
    if (v.includes('DELAY') || v.includes('POSTPONE') || v.includes('NOT_RECOMMENDED') || v.includes('ELEVATED') || v.includes('CAUTION') || v.includes('MONITOR')) {
      return { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.3)' };
    }
    return { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)' };
  };

  const getRiskStyle = (level: string) => {
    const l = level.toUpperCase();
    if (l === 'CRITICAL') return { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)' };
    if (l === 'HIGH') return { color: '#f97316', bg: 'rgba(249, 115, 22, 0.2)' };
    if (l === 'MEDIUM') return { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.2)' };
    return { color: '#10b981', bg: 'rgba(16, 185, 129, 0.2)' };
  };

  const advisoryItems: AdvisoryRecommendation[] = advisoryData?.advisories || advisoryData?.recommendations || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Sector Navigation & Dynamic Controls */}
      <div className="glass-panel" style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {[
            { id: 'agriculture', label: '🌾 Agriculture', desc: 'Irrigation & Spraying' },
            { id: 'disaster', label: '🚨 Disaster Response', desc: 'Flood & Severe Weather' },
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
                transition: 'all 0.15s ease'
              }}
            >
              {sec.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
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
            <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>({latitude.toFixed(2)}°, {longitude.toFixed(2)}°)</span>
          </div>

          {activeSector === 'agriculture' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
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

              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  onClick={() => setHorizonDays(1)}
                  style={{
                    padding: '0.35rem 0.6rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: horizonDays === 1 ? '#0284c7' : 'rgba(30, 41, 59, 0.6)',
                    color: '#fff',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Tomorrow
                </button>
                <button
                  onClick={() => setHorizonDays(4)}
                  style={{
                    padding: '0.35rem 0.6rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: horizonDays === 4 ? '#0284c7' : 'rgba(30, 41, 59, 0.6)',
                    color: '#fff',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  4-Day Horizon
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Advisory Content Cards */}
      {loading ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#38bdf8' }}>
          ⚡ Evaluating domain meteorological triggers & dynamic sector rules...
        </div>
      ) : advisoryData ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {advisoryItems.map((rec, i) => {
            const verdict = rec.recommendation || rec.verdict || 'NORMAL';
            const vStyle = getVerdictStyle(verdict);
            const rStyle = getRiskStyle(rec.risk_level || 'LOW');
            const basisList = rec.basis || rec.reasons || [];
            const recActions = rec.recommended_actions || rec.actionable_steps || [];
            const avoidActions = rec.avoid_actions || [];

            return (
              <div
                key={i}
                className="glass-panel"
                style={{
                  padding: '1.5rem',
                  borderTop: `4px solid ${vStyle.color}`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '1rem'
                }}
              >
                <div>
                  {/* Card Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1.6rem' }}>{rec.icon}</span>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                        {rec.title}
                      </h4>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '3px 8px',
                        borderRadius: '6px',
                        background: vStyle.bg,
                        color: vStyle.color,
                        border: `1px solid ${vStyle.border}`
                      }}>
                        {verdict.replace(/_/g, ' ')}
                      </span>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        padding: '1px 6px',
                        borderRadius: '4px',
                        background: rStyle.bg,
                        color: rStyle.color
                      }}>
                        Risk: {rec.risk_level} {rec.risk_score ? `(${Math.round(rec.risk_score)}/100)` : ''}
                      </span>
                    </div>
                  </div>

                  {/* Weather Trigger Summary */}
                  {rec.weather_trigger && Object.keys(rec.weather_trigger).length > 0 && (
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '6px',
                      background: 'rgba(15, 23, 42, 0.4)',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      marginBottom: '0.75rem',
                      fontSize: '0.75rem',
                      color: '#94a3b8'
                    }}>
                      {rec.weather_trigger.rain_probability_pct !== undefined && (
                        <span>🌧️ Rain Chance: <strong style={{ color: '#f8fafc' }}>{rec.weather_trigger.rain_probability_pct}%</strong></span>
                      )}
                      {rec.weather_trigger.expected_precipitation_mm !== undefined && (
                        <span>💧 Rain Sum: <strong style={{ color: '#f8fafc' }}>{rec.weather_trigger.expected_precipitation_mm} mm</strong></span>
                      )}
                      {rec.weather_trigger.wind_speed_kmh !== undefined && (
                        <span>💨 Wind: <strong style={{ color: '#f8fafc' }}>{rec.weather_trigger.wind_speed_kmh} km/h</strong></span>
                      )}
                      {rec.weather_trigger.temperature_c !== undefined && (
                        <span>🌡️ Temp: <strong style={{ color: '#f8fafc' }}>{rec.weather_trigger.temperature_c}°C</strong></span>
                      )}
                    </div>
                  )}

                  {/* Weather Trigger & Basis */}
                  <div style={{ marginBottom: '0.85rem' }}>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                      Weather Trigger & Basis:
                    </div>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.82rem', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {basisList.map((r, ri) => (
                        <li key={ri}>{r}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Multi-Day Horizon Breakdown (If available) */}
                  {rec.horizon_breakdown && rec.horizon_breakdown.length > 0 && (
                    <div style={{ marginBottom: '0.85rem', background: 'rgba(15, 23, 42, 0.5)', padding: '0.6rem', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                        4-Day Forecast Trajectory:
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '6px' }}>
                        {rec.horizon_breakdown.map((b, bi) => (
                          <div key={bi} style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '0.4rem 0.5rem', borderRadius: '6px', fontSize: '0.72rem' }}>
                            <div style={{ fontWeight: 700, color: '#f8fafc' }}>{b.day.split(' ')[0]}</div>
                            <div style={{ color: '#94a3b8' }}>{b.condition} ({b.rain_probability_pct}%)</div>
                            <div style={{ color: b.irrigation_verdict === 'DELAY' ? '#f59e0b' : '#10b981', fontWeight: 600 }}>
                              Irr: {b.irrigation_verdict}
                            </div>
                            <div style={{ color: b.spraying_verdict === 'FAVORABLE' ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
                              Spray: {b.spraying_verdict}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommended Action */}
                  {recActions.length > 0 && (
                    <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '0.65rem 0.75rem', borderRadius: '8px', marginBottom: '0.65rem' }}>
                      <div style={{ fontSize: '0.72rem', color: '#34d399', fontWeight: 700, textTransform: 'uppercase', marginBottom: '3px' }}>
                        Recommended Action:
                      </div>
                      <ul style={{ paddingLeft: '1.2rem', fontSize: '0.8rem', color: '#e2e8f0', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {recActions.map((s, si) => (
                          <li key={si}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Avoid Actions */}
                  {avoidActions.length > 0 && (
                    <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '0.65rem 0.75rem', borderRadius: '8px', marginBottom: '0.65rem' }}>
                      <div style={{ fontSize: '0.72rem', color: '#f87171', fontWeight: 700, textTransform: 'uppercase', marginBottom: '3px' }}>
                        Avoid:
                      </div>
                      <ul style={{ paddingLeft: '1.2rem', fontSize: '0.8rem', color: '#fca5a5', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {avoidActions.map((a, ai) => (
                          <li key={ai}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Limitations */}
                  {rec.limitations && rec.limitations.length > 0 && (
                    <div style={{ fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic', marginTop: '0.4rem' }}>
                      ⚠️ {rec.limitations[0]}
                    </div>
                  )}
                </div>

                {/* Card Footer */}
                <div style={{
                  marginTop: '0.75rem',
                  paddingTop: '0.6rem',
                  borderTop: '1px solid rgba(255,255,255,0.06)',
                  fontSize: '0.72rem',
                  color: '#64748b',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '4px'
                }}>
                  <span>Valid until: <strong style={{ color: '#94a3b8' }}>{rec.valid_until}</strong></span>
                  <span>Source: <strong style={{ color: '#94a3b8' }}>{(rec.sources || [advisoryData.source || 'Open-Meteo forecast']).join(', ')}</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

    </div>
  );
};
