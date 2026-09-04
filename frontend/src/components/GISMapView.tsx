import React, { useEffect, useRef, useState } from 'react';
import { Layers, AlertTriangle, MapPin } from './Icons';

interface GISMapViewProps {
  latitude: number;
  longitude: number;
  locationName: string;
}

export const GISMapView: React.FC<GISMapViewProps> = ({ latitude, longitude, locationName }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const [activeLayer, setActiveLayer] = useState<'standard' | 'precip' | 'temp' | 'wind'>('standard');
  const [showHazards, setShowHazards] = useState(true);

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

      mapInstanceRef.current = map;
    } else {
      mapInstanceRef.current.setView([latitude, longitude], 7);
    }

    const map = mapInstanceRef.current;

    // Clear existing markers/layers
    map.eachLayer((layer: any) => {
      if (layer instanceof L.Marker || layer instanceof L.Circle) {
        map.removeLayer(layer);
      }
    });

    // Add User/Target Location Marker
    const userMarker = L.circle([latitude, longitude], {
      color: '#38bdf8',
      fillColor: '#0284c7',
      fillOpacity: 0.8,
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

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', position: 'relative' }}>
      
      {/* Top Header & Layer Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={18} color="#38bdf8" />
            Interactive Meteorological GIS Map
          </h3>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            PostGIS Georeferenced Coordinates & Official IMD Hazard Zones
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

      {/* Leaflet Map Canvas */}
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '420px',
          borderRadius: '14px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          zIndex: 1
        }}
      />

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
