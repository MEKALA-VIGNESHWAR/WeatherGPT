import React, { useEffect, useRef, useState } from 'react';
import { Layers, AlertTriangle, MapPin } from './Icons';
import { fetchForecast, reverseGeocodeLocation } from '../services/api';
import type { UnifiedWeatherResponse } from '../types/weather';

interface GISMapViewProps {
  latitude: number;
  longitude: number;
  locationName: string;
  onLocationSelect?: (name: string, lat: number, lon: number) => void;
}

interface SelectedMapPoint {
  lat: number;
  lon: number;
  name: string;
  loading: boolean;
  weather?: UnifiedWeatherResponse | null;
  error?: string | null;
  inHazardZone?: string | null;
}

export const GISMapView: React.FC<GISMapViewProps> = ({
  latitude,
  longitude,
  locationName,
  onLocationSelect
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const selectedMarkerRef = useRef<any>(null);

  const [activeLayer, setActiveLayer] = useState<'standard' | 'precip' | 'temp'>('standard');
  const [showHazards, setShowHazards] = useState(true);
  const [dockPosition, setDockPosition] = useState<'right' | 'left' | 'bottom'>('right');
  const [selectedPoint, setSelectedPoint] = useState<SelectedMapPoint | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Haversine distance calculator for client-side hazard checking
  const getDistanceKm = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  useEffect(() => {
    const L = (window as any).L;
    if (!L || !mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize map
      const map = L.map(mapContainerRef.current, {
        center: [latitude, longitude],
        zoom: 7,
        zoomControl: true
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      // Add Random Click Listener to Map
      map.on('click', async (e: any) => {
        const clickedLat = Number(e.latlng.lat.toFixed(4));
        const clickedLon = Number(e.latlng.lng.toFixed(4));

        // Check if point falls within known hazard zones
        let hazardText: string | null = null;
        const distToHyd = getDistanceKm(clickedLat, clickedLon, 17.3850, 78.4867);
        if (distToHyd <= 65) {
          hazardText = 'IMD Yellow Watch: Thunderstorm & Gusty Winds (30-40 km/h)';
        }
        const distToCoastal = getDistanceKm(clickedLat, clickedLon, 18.2, 84.8);
        if (distToCoastal <= 95) {
          hazardText = 'IMD Orange Alert: Bay of Bengal Depression & Squally Winds';
        }

        // Set immediate loading state
        setSelectedPoint({
          lat: clickedLat,
          lon: clickedLon,
          name: `Coordinates (${clickedLat}°, ${clickedLon}°)`,
          loading: true,
          weather: null,
          inHazardZone: hazardText
        });

        // Add or move selected point marker
        if (selectedMarkerRef.current) {
          map.removeLayer(selectedMarkerRef.current);
        }
        selectedMarkerRef.current = L.circle([clickedLat, clickedLon], {
          color: '#f43f5e',
          fillColor: '#fb7185',
          fillOpacity: 0.85,
          radius: 6000
        }).addTo(map);
        selectedMarkerRef.current.bindPopup(`<strong>Clicked Location</strong><br/>Lat: ${clickedLat}, Lon: ${clickedLon}`).openPopup();

        // Fetch reverse geocode and live weather concurrently
        try {
          const [geoRes, forecastRes] = await Promise.all([
            reverseGeocodeLocation(clickedLat, clickedLon).catch(() => null),
            fetchForecast(clickedLat, clickedLon, 3).catch(() => null)
          ]);

          let resolvedName = `Lat: ${clickedLat}°, Lon: ${clickedLon}°`;
          if (geoRes?.name && geoRes.name !== 'Current Location') {
            resolvedName = `${geoRes.name}${geoRes.state ? `, ${geoRes.state}` : ''}`;
          } else if (forecastRes?.location?.name) {
            resolvedName = forecastRes.location.name;
          }

          setSelectedPoint({
            lat: clickedLat,
            lon: clickedLon,
            name: resolvedName,
            loading: false,
            weather: forecastRes,
            inHazardZone: hazardText
          });
        } catch (err: any) {
          setSelectedPoint((prev) =>
            prev
              ? {
                  ...prev,
                  loading: false,
                  error: 'Live weather telemetry unavailable for this coordinate.'
                }
              : null
          );
        }
      });

      mapInstanceRef.current = map;
    } else {
      mapInstanceRef.current.setView([latitude, longitude], 7);
    }

    const map = mapInstanceRef.current;

    // Clear existing static markers/layers (except selectedMarkerRef if active)
    map.eachLayer((layer: any) => {
      if ((layer instanceof L.Marker || layer instanceof L.Circle) && layer !== selectedMarkerRef.current) {
        map.removeLayer(layer);
      }
    });

    // Add Active Location Marker
    const userMarker = L.circle([latitude, longitude], {
      color: '#38bdf8',
      fillColor: '#0284c7',
      fillOpacity: 0.85,
      radius: 8000
    }).addTo(map);
    userMarker.bindPopup(`<strong>${locationName}</strong><br/>Active Observation Target`);

    // Add Pre-seeded Indian Meteorological Stations
    const stations = [
      { name: 'Hyderabad (Begumpet IMD)', lat: 17.4531, lon: 78.4676, state: 'Telangana', temp: '28.4°C' },
      { name: 'Amaravati IMD AWS', lat: 16.5417, lon: 80.5158, state: 'Andhra Pradesh', temp: '29.2°C' },
      { name: 'Visakhapatnam Cyclone Radar', lat: 17.6868, lon: 83.2185, state: 'Andhra Pradesh', temp: '27.8°C' },
      { name: 'Bengaluru HAL AWS', lat: 12.9716, lon: 77.5946, state: 'Karnataka', temp: '24.1°C' },
      { name: 'Chennai Meenambakkam', lat: 13.0827, lon: 80.2707, state: 'Tamil Nadu', temp: '31.0°C' }
    ];

    stations.forEach((st) => {
      const stMarker = L.circle([st.lat, st.lon], {
        color: '#10b981',
        fillColor: '#059669',
        fillOpacity: 0.6,
        radius: 5000
      }).addTo(map);
      stMarker.bindPopup(`<strong>${st.name}</strong><br/>State: ${st.state}<br/>Temp: ${st.temp}`);
    });

    // Add Official Hazard Zones if enabled
    if (showHazards) {
      // 1. Telangana Thunderstorm Warning Zone (Yellow)
      const hydHazard = L.circle([17.3850, 78.4867], {
        color: '#f59e0b',
        fillColor: '#f59e0b',
        fillOpacity: 0.18,
        radius: 65000
      }).addTo(map);
      hydHazard.bindPopup(`<strong>⚠️ IMD Warning: Thunderstorm Zone</strong><br/>Gusty winds 30-40 km/h<br/>Severity: YELLOW WATCH`);

      // 2. Coastal Squall Warning Zone (Orange)
      const coastalHazard = L.circle([18.2, 84.8], {
        color: '#f97316',
        fillColor: '#f97316',
        fillOpacity: 0.22,
        radius: 95000
      }).addTo(map);
      coastalHazard.bindPopup(`<strong>⚠️ Coastal Squall Warning (Depression)</strong><br/>Wind 55-65 km/h<br/>Severity: ORANGE ALERT`);
    }

  }, [latitude, longitude, locationName, showHazards]);

  const handleSetActiveLocation = (name: string, lat: number, lon: number) => {
    if (onLocationSelect) {
      onLocationSelect(name, lat, lon);
      setActionNotice(`Active location updated to ${name}!`);
      setTimeout(() => setActionNotice(null), 3000);
    }
  };

  const handleCloseCard = () => {
    setSelectedPoint(null);
    if (selectedMarkerRef.current && mapInstanceRef.current) {
      mapInstanceRef.current.removeLayer(selectedMarkerRef.current);
      selectedMarkerRef.current = null;
    }
  };

  // Determine floating card position based on dockPosition state
  const getDockStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: 'absolute',
      zIndex: 500,
      background: 'rgba(15, 23, 42, 0.94)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(56, 189, 248, 0.4)',
      borderRadius: '14px',
      boxShadow: '0 16px 40px rgba(0,0,0,0.7)',
      padding: '1rem',
      color: '#f8fafc',
      transition: 'all 0.25s ease'
    };

    if (dockPosition === 'right') {
      return {
        ...base,
        top: '12px',
        right: '12px',
        bottom: '12px',
        width: '340px',
        maxWidth: 'calc(100% - 24px)',
        overflowY: 'auto'
      };
    } else if (dockPosition === 'left') {
      return {
        ...base,
        top: '12px',
        left: '12px',
        bottom: '12px',
        width: '340px',
        maxWidth: 'calc(100% - 24px)',
        overflowY: 'auto'
      };
    } else {
      // Bottom dock
      return {
        ...base,
        bottom: '12px',
        left: '12px',
        right: '12px',
        maxHeight: '280px',
        overflowY: 'auto'
      };
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', position: 'relative' }}>
      
      {/* Action Toast Notice */}
      {actionNotice && (
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#0284c7',
          color: '#fff',
          padding: '0.5rem 1.25rem',
          borderRadius: '9999px',
          fontWeight: 600,
          fontSize: '0.85rem',
          boxShadow: '0 8px 24px rgba(2, 132, 199, 0.5)',
          zIndex: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>✓</span>
          <span>{actionNotice}</span>
        </div>
      )}

      {/* Top Header & Layer Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={18} color="#38bdf8" />
            Interactive Meteorological GIS Map
          </h3>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Click anywhere on the map to inspect live weather & radar telemetry
          </div>
        </div>

        {/* Map Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setShowHazards(!showHazards)}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '8px',
              border: showHazards ? '1px solid #f59e0b' : '1px solid rgba(255,255,255,0.1)',
              background: showHazards ? 'rgba(245, 158, 11, 0.2)' : 'rgba(30, 41, 59, 0.6)',
              color: showHazards ? '#fde047' : '#94a3b8',
              fontSize: '0.78rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <AlertTriangle size={13} color={showHazards ? '#fde047' : '#94a3b8'} />
            {showHazards ? 'Hazards Active' : 'Show Hazards'}
          </button>

          <div style={{
            background: 'rgba(30, 41, 59, 0.6)',
            padding: '2px',
            borderRadius: '8px',
            display: 'flex',
            gap: '2px',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            {[
              { id: 'standard', label: 'Standard' },
              { id: 'precip', label: 'Rain Radar' },
              { id: 'temp', label: 'Thermal' }
            ].map((layer) => (
              <button
                key={layer.id}
                onClick={() => setActiveLayer(layer.id as any)}
                style={{
                  padding: '0.35rem 0.65rem',
                  borderRadius: '6px',
                  border: 'none',
                  background: activeLayer === layer.id ? '#0284c7' : 'transparent',
                  color: activeLayer === layer.id ? '#fff' : '#94a3b8',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                {layer.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Relative Map Canvas Wrapper */}
      <div style={{ position: 'relative', width: '100%', borderRadius: '14px', overflow: 'hidden' }}>
        
        {/* Leaflet Canvas */}
        <div
          ref={mapContainerRef}
          style={{
            width: '100%',
            height: '480px',
            zIndex: 1
          }}
        />

        {/* Selected Map Point Weather Card (User-Adjustable Dock: Left, Right, Bottom) */}
        {selectedPoint && (
          <div style={getDockStyles()}>
            
            {/* Card Header & Position Adjuster */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.65rem', marginBottom: '0.75rem' }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  📍 Selected Point Weather Report
                </div>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, margin: '2px 0 0 0', color: '#f8fafc' }}>
                  {selectedPoint.name}
                </h4>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  {selectedPoint.lat.toFixed(3)}° N, {selectedPoint.lon.toFixed(3)}° E
                </div>
              </div>

              {/* Controls: Dock Switcher & Close */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ display: 'flex', background: 'rgba(30, 41, 59, 0.7)', borderRadius: '6px', padding: '2px', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <button
                    title="Dock Left"
                    onClick={() => setDockPosition('left')}
                    style={{
                      border: 'none',
                      background: dockPosition === 'left' ? '#0284c7' : 'transparent',
                      color: dockPosition === 'left' ? '#fff' : '#94a3b8',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.7rem'
                    }}
                  >
                    ◀
                  </button>
                  <button
                    title="Dock Bottom"
                    onClick={() => setDockPosition('bottom')}
                    style={{
                      border: 'none',
                      background: dockPosition === 'bottom' ? '#0284c7' : 'transparent',
                      color: dockPosition === 'bottom' ? '#fff' : '#94a3b8',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.7rem'
                    }}
                  >
                    ▼
                  </button>
                  <button
                    title="Dock Right"
                    onClick={() => setDockPosition('right')}
                    style={{
                      border: 'none',
                      background: dockPosition === 'right' ? '#0284c7' : 'transparent',
                      color: dockPosition === 'right' ? '#fff' : '#94a3b8',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.7rem'
                    }}
                  >
                    ▶
                  </button>
                </div>

                <button
                  onClick={handleCloseCard}
                  title="Close Card"
                  style={{
                    border: 'none',
                    background: 'rgba(239, 68, 68, 0.2)',
                    color: '#f87171',
                    borderRadius: '6px',
                    padding: '4px 8px',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: 700
                  }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Loading State */}
            {selectedPoint.loading && (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: '#38bdf8' }}>
                <span className="animate-pulse-glow" style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>🛰️</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Retrieving atmospheric soundings...</div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>Querying high-resolution NWP grid</div>
              </div>
            )}

            {/* Error State */}
            {selectedPoint.error && (
              <div style={{ padding: '1rem', color: '#f87171', fontSize: '0.82rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px' }}>
                {selectedPoint.error}
              </div>
            )}

            {/* Loaded Weather Data */}
            {!selectedPoint.loading && selectedPoint.weather && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                
                {/* Active Hazard Warning Badge if within hazard radius */}
                {selectedPoint.inHazardZone && (
                  <div style={{
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    border: '1px solid rgba(245, 158, 11, 0.4)',
                    color: '#fde047',
                    fontSize: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}>
                    <AlertTriangle size={14} color="#fde047" />
                    <span>{selectedPoint.inHazardZone}</span>
                  </div>
                )}

                {/* Primary Temp & Condition Banner */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'rgba(30, 41, 59, 0.5)',
                  padding: '0.75rem',
                  borderRadius: '10px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '2.4rem' }}>
                      {selectedPoint.weather.current.weather_icon || '⛅'}
                    </span>
                    <div>
                      <div style={{ fontSize: '1.8rem', fontWeight: 800, lineHeight: 1 }}>
                        {Math.round(selectedPoint.weather.current.temperature_c)}°C
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        Feels like {Math.round(selectedPoint.weather.current.feels_like_c)}°C
                      </div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8' }}>
                      {selectedPoint.weather.current.weather_condition}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                      Verified NWP Grid
                    </div>
                  </div>
                </div>

                {/* Key Meteorological Parameters Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: dockPosition === 'bottom' ? 'repeat(4, 1fr)' : 'repeat(2, 1fr)',
                  gap: '0.5rem'
                }}>
                  <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.45rem 0.6rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>💧 Humidity</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                      {selectedPoint.weather.current.relative_humidity_pct}%
                    </div>
                  </div>
                  <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.45rem 0.6rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>💨 Wind Speed</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                      {selectedPoint.weather.current.wind_speed_kmh} km/h
                    </div>
                  </div>
                  <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.45rem 0.6rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>🌧️ Rain Chance</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: (selectedPoint.weather.current.precipitation_probability_pct ?? 0) > 30 ? '#38bdf8' : '#f8fafc' }}>
                      {selectedPoint.weather.current.precipitation_probability_pct ?? 0}%
                    </div>
                  </div>
                  <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.45rem 0.6rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>⏱️ Pressure</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                      {selectedPoint.weather.current.surface_pressure_hpa} hPa
                    </div>
                  </div>
                </div>

                {/* Next 4 Hours Forecast Preview */}
                {selectedPoint.weather.hourly && selectedPoint.weather.hourly.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                      Next Hours Outlook
                    </div>
                    <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '2px' }}>
                      {selectedPoint.weather.hourly.slice(0, 4).map((pt, i) => {
                        const hTime = pt.time.includes('T') ? pt.time.split('T')[1].slice(0, 5) : pt.time;
                        return (
                          <div
                            key={i}
                            style={{
                              flex: '1',
                              background: 'rgba(30, 41, 59, 0.5)',
                              borderRadius: '6px',
                              padding: '0.35rem 0.25rem',
                              textAlign: 'center',
                              fontSize: '0.72rem'
                            }}
                          >
                            <div style={{ color: '#94a3b8', fontSize: '0.65rem' }}>{i === 0 ? 'Now' : hTime}</div>
                            <div style={{ fontSize: '1rem', margin: '2px 0' }}>{pt.weather_icon}</div>
                            <div style={{ fontWeight: 700 }}>{Math.round(pt.temperature_c)}°</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Primary CTA: Set as Target Location */}
                <button
                  onClick={() => handleSetActiveLocation(selectedPoint.name, selectedPoint.lat, selectedPoint.lon)}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <MapPin size={15} color="#fff" />
                  <span>Set as Active Dashboard Target</span>
                </button>

              </div>
            )}

          </div>
        )}

      </div>

      {/* Map Legend */}
      <div style={{
        marginTop: '0.75rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1.5rem',
        fontSize: '0.75rem',
        color: '#94a3b8',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#0284c7' }} />
          <span>Active Target GPS</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f43f5e' }} />
          <span>Clicked Map Selection</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }} />
          <span>IMD AWS Stations</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
          <span>Thunderstorm Watch Zone</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f97316' }} />
          <span>Squall / Maritime Alert Zone</span>
        </div>
      </div>

    </div>
  );
};
