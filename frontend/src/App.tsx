import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { WeatherCard } from './components/WeatherCard';
import { HourlySlider } from './components/HourlySlider';
import { ForecastGrid } from './components/ForecastGrid';
import { AlertBanner } from './components/AlertBanner';
import { ChatDrawer } from './components/ChatDrawer';
import { GISMapView } from './components/GISMapView';
import { SectorAdvisoryView } from './components/SectorAdvisoryView';
import { ClimateTrendsView } from './components/ClimateTrendsView';
import { AdminView } from './components/AdminView';
import { fetchForecast, fetchActiveAlerts } from './services/api';
import type { UnifiedWeatherResponse } from './types/weather';
import type { WeatherAlert } from './types/alert';
import { Sparkles, Layers, Tractor, Activity, CloudRain } from './components/Icons';

export const App: React.FC = () => {
  const [currentLocation, setCurrentLocation] = useState('Hyderabad');
  const [latitude, setLatitude] = useState(17.3850);
  const [longitude, setLongitude] = useState(78.4867);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [userRole, setUserRole] = useState('citizen');
  
  // URL Hash Sync for robust routing (#dashboard, #chat, #map, #advisories, #climate, #admin)
  const getInitialTab = () => {
    const hash = window.location.hash.replace('#', '').toLowerCase();
    if (['dashboard', 'chat', 'map', 'advisories', 'climate', 'admin'].includes(hash)) {
      return hash;
    }
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [weatherData, setWeatherData] = useState<UnifiedWeatherResponse | null>(null);
  const [activeAlerts, setActiveAlerts] = useState<WeatherAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sync hash with activeTab
  const handleTabSwitch = (tabId: string) => {
    setActiveTab(tabId);
    window.location.hash = `#${tabId}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Listen for browser back/forward button hash changes
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (['dashboard', 'chat', 'map', 'advisories', 'climate', 'admin'].includes(hash)) {
        setActiveTab(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Fetch forecast and alerts whenever location changes
  useEffect(() => {
    loadWeatherData();
  }, [latitude, longitude]);

  // WebSocket for real-time alert notifications
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://localhost:8000/ws/alerts');
      ws.onopen = () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'SUBSCRIBE_LOCATION',
            latitude,
            longitude,
            location_name: currentLocation
          }));
        }
      };
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if ((payload.type === 'INITIAL_ALERTS' || payload.type === 'LOCATION_ALERTS') && payload.data?.alerts) {
            setActiveAlerts(payload.data.alerts);
          }
        } catch {
          // ignore
        }
      };
    } catch {
      // Non-blocking WebSocket fallback
    }

    return () => {
      if (ws) ws.close();
    };
  }, [latitude, longitude, currentLocation]);

  const loadWeatherData = async (overrideLat?: number, overrideLon?: number, overrideName?: string) => {
    const lat = overrideLat ?? latitude;
    const lon = overrideLon ?? longitude;
    const loc = overrideName ?? currentLocation;
    setLoading(true);
    setError(null);
    try {
      const [forecastRes, alertsRes] = await Promise.all([
        fetchForecast(lat, lon, 7),
        fetchActiveAlerts(lat, lon, loc)
      ]);
      setWeatherData(forecastRes);
      if (alertsRes && Array.isArray(alertsRes.alerts)) {
        setActiveAlerts(alertsRes.alerts);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to weather data services.');
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (name: string, lat: number, lon: number) => {
    setCurrentLocation(name);
    setLatitude(lat);
    setLongitude(lon);
    loadWeatherData(lat, lon, name);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Top Navbar */}
      <Navbar
        currentLocation={currentLocation}
        onLocationChange={handleLocationSelect}
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
        userRole={userRole}
        onUserRoleChange={setUserRole}
        activeTab={activeTab}
        setActiveTab={handleTabSwitch}
        isDemoMode={weatherData?.trust.is_demo_data}
      />

      {/* Main Content Area */}
      <main style={{ maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '1.5rem', flex: 1 }}>
        
        {/* Official Warnings Banner (Global) */}
        <AlertBanner alerts={activeAlerts} />

        {/* Global Error Banner if backend unreachable */}
        {error && (
          <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem', borderColor: '#ef4444', color: '#fca5a5', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong>Service Notice:</strong> {error}
            </div>
            <button
              onClick={() => loadWeatherData()}
              style={{ padding: '0.4rem 0.8rem', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* TAB 1: DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Quick Section Traverse Bar */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem'
            }}>
              <div
                onClick={() => handleTabSwitch('chat')}
                className="glass-panel"
                style={{
                  padding: '0.75rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: 'rgba(2, 132, 199, 0.12)',
                  borderColor: 'rgba(56, 189, 248, 0.25)'
                }}
              >
                <span style={{ fontSize: '1.4rem' }}>💬</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f8fafc' }}>Ask WeatherGPT</div>
                  <div style={{ fontSize: '0.7rem', color: '#38bdf8' }}>Open Full Chat →</div>
                </div>
              </div>

              <div
                onClick={() => handleTabSwitch('map')}
                className="glass-panel"
                style={{
                  padding: '0.75rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: 'rgba(16, 185, 129, 0.1)',
                  borderColor: 'rgba(16, 185, 129, 0.25)'
                }}
              >
                <span style={{ fontSize: '1.4rem' }}>🗺️</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f8fafc' }}>GIS Weather Map</div>
                  <div style={{ fontSize: '0.7rem', color: '#10b981' }}>Radar & Hazards →</div>
                </div>
              </div>

              <div
                onClick={() => handleTabSwitch('advisories')}
                className="glass-panel"
                style={{
                  padding: '0.75rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: 'rgba(245, 158, 11, 0.1)',
                  borderColor: 'rgba(245, 158, 11, 0.25)'
                }}
              >
                <span style={{ fontSize: '1.4rem' }}>🌾</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f8fafc' }}>Crop Advisories</div>
                  <div style={{ fontSize: '0.7rem', color: '#f59e0b' }}>Irrigation & Spraying →</div>
                </div>
              </div>

              <div
                onClick={() => handleTabSwitch('climate')}
                className="glass-panel"
                style={{
                  padding: '0.75rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: 'rgba(99, 102, 241, 0.1)',
                  borderColor: 'rgba(99, 102, 241, 0.25)'
                }}
              >
                <span style={{ fontSize: '1.4rem' }}>📊</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f8fafc' }}>Climate Trends</div>
                  <div style={{ fontSize: '0.7rem', color: '#818cf8' }}>7-Day Rainfall Stats →</div>
                </div>
              </div>
            </div>

            {/* Weather Hero Card & Embedded Assistant */}
            {loading && !weatherData ? (
              <div className="glass-panel" style={{ padding: '3.5rem', textAlign: 'center', color: '#38bdf8' }}>
                <span className="animate-pulse-glow" style={{ fontSize: '2.5rem', display: 'block', marginBottom: '0.75rem' }}>☁️</span>
                <h3>Loading verified meteorological grid observations...</h3>
              </div>
            ) : weatherData ? (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem', alignItems: 'stretch' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <WeatherCard
                      weather={weatherData.current}
                      locationName={weatherData.location.name || currentLocation}
                      trust={weatherData.trust}
                    />
                    <HourlySlider hourly={weatherData.hourly} />
                  </div>

                  {/* Embedded Conversational Assistant Card */}
                  <div>
                    <ChatDrawer
                      currentLocation={currentLocation}
                      latitude={latitude}
                      longitude={longitude}
                      selectedLanguage={selectedLanguage}
                      userRole={userRole}
                    />
                  </div>
                </div>

                {/* 7-Day Forecast Grid */}
                <ForecastGrid daily={weatherData.daily} />

                {/* GIS Map Preview on Dashboard */}
                <GISMapView
                  latitude={latitude}
                  longitude={longitude}
                  locationName={currentLocation}
                  onLocationSelect={handleLocationSelect}
                />
              </>
            ) : null}

          </div>
        )}

        {/* TAB 2: FULL CHAT ASSISTANT */}
        {activeTab === 'chat' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                  Conversational Weather Intelligence
                </h2>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Ask questions in {selectedLanguage.toUpperCase()} or use voice input for instant decision support.
                </p>
              </div>
              <button
                onClick={() => handleTabSwitch('dashboard')}
                style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', padding: '0.4rem 0.9rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ← Back to Dashboard
              </button>
            </div>

            <ChatDrawer
              currentLocation={currentLocation}
              latitude={latitude}
              longitude={longitude}
              selectedLanguage={selectedLanguage}
              userRole={userRole}
              isOpenAsFullPage={true}
            />
          </div>
        )}

        {/* TAB 3: GIS MAP */}
        {activeTab === 'map' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                  GIS Geospatial Weather Map & Hazard Radar
                </h2>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Interactive OpenStreetMap canvas with IMD weather stations and active hazard zones.
                </p>
              </div>
              <button
                onClick={() => handleTabSwitch('dashboard')}
                style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', padding: '0.4rem 0.9rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ← Back to Dashboard
              </button>
            </div>

            <GISMapView
              latitude={latitude}
              longitude={longitude}
              locationName={currentLocation}
              onLocationSelect={handleLocationSelect}
            />
          </div>
        )}

        {/* TAB 4: ADVISORIES */}
        {activeTab === 'advisories' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                  Sector Decision Support Advisories
                </h2>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Actionable guidance for Agriculture, Disaster Management, Commuters, Marine, and Aviation.
                </p>
              </div>
              <button
                onClick={() => handleTabSwitch('dashboard')}
                style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', padding: '0.4rem 0.9rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ← Back to Dashboard
              </button>
            </div>

            <SectorAdvisoryView
              latitude={latitude}
              longitude={longitude}
              locationName={currentLocation}
            />
          </div>
        )}

        {/* TAB 5: CLIMATE TRENDS */}
        {activeTab === 'climate' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                  Historical Climate Trends & Anomalies
                </h2>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  7-day observed rainfall distribution and seasonal departure norms.
                </p>
              </div>
              <button
                onClick={() => handleTabSwitch('dashboard')}
                style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', padding: '0.4rem 0.9rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ← Back to Dashboard
              </button>
            </div>

            <ClimateTrendsView
              latitude={latitude}
              longitude={longitude}
              locationName={currentLocation}
            />
          </div>
        )}

        {/* TAB 6: ADMIN */}
        {activeTab === 'admin' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                  Platform Operations & Health Telemetry
                </h2>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Real-time system health, API latencies, provider synchronization, and feedback metrics.
                </p>
              </div>
              <button
                onClick={() => handleTabSwitch('dashboard')}
                style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', padding: '0.4rem 0.9rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ← Back to Dashboard
              </button>
            </div>

            <AdminView />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{
        background: 'rgba(11, 15, 25, 0.9)',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '1.5rem',
        marginTop: '3rem',
        textAlign: 'center',
        fontSize: '0.82rem',
        color: '#64748b'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <strong>WeatherGPT</strong> — Smart India Hackathon 2026. Built on "Data → Context → Risk → Decision"
          </div>
          <div>
            Meteorological layer over IMD, Open-Meteo, ECMWF, and NOAA NWP Infrastructure.
          </div>
        </div>
      </footer>

    </div>
  );
};

export default App;
