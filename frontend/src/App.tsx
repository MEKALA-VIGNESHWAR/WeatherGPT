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
import { UnifiedWeatherResponse } from './types/weather';
import { WeatherAlert } from './types/alert';

export const App: React.FC = () => {
  const [currentLocation, setCurrentLocation] = useState('Hyderabad');
  const [latitude, setLatitude] = useState(17.3850);
  const [longitude, setLongitude] = useState(78.4867);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [userRole, setUserRole] = useState('citizen');
  const [activeTab, setActiveTab] = useState('dashboard');
  
  const [weatherData, setWeatherData] = useState<UnifiedWeatherResponse | null>(null);
  const [activeAlerts, setActiveAlerts] = useState<WeatherAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch forecast and alerts whenever location changes
  useEffect(() => {
    loadWeatherData();
  }, [latitude, longitude]);

  // WebSocket for real-time alert notifications
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://localhost:8000/ws/alerts');
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'INITIAL_ALERTS' && payload.data?.alerts) {
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
  }, []);

  const loadWeatherData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [forecastRes, alertsRes] = await Promise.all([
        fetchForecast(latitude, longitude, 7),
        fetchActiveAlerts(latitude, longitude, currentLocation)
      ]);
      setWeatherData(forecastRes);
      if (alertsRes?.alerts) {
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
        setActiveTab={setActiveTab}
        isDemoMode={weatherData?.trust.is_demo_data}
      />

      {/* Main Content Area */}
      <main style={{ maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '1.5rem', flex: 1 }}>
        
        {/* Official Warnings Banner (Global) */}
        <AlertBanner alerts={activeAlerts} />

        {/* Loading / Error States */}
        {loading && !weatherData && (
          <div className="glass-panel" style={{ padding: '4rem', textAlign: 'center', color: '#38bdf8' }}>
            <span className="animate-pulse-glow" style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>☁️</span>
            <h3>Retrieving meteorological observations and NWP model runs...</h3>
          </div>
        )}

        {error && !weatherData && (
          <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderColor: '#ef4444', color: '#fca5a5' }}>
            <h4>Unable to reach weather backend.</h4>
            <p style={{ margin: '0.5rem 0', fontSize: '0.9rem' }}>{error}</p>
            <button
              onClick={loadWeatherData}
              style={{ padding: '0.5rem 1rem', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* View Routing */}
        {weatherData && (
          <>
            {activeTab === 'dashboard' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                
                {/* Top Row: Current Weather Hero & Chat Drawer */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem', alignItems: 'stretch' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <WeatherCard
                      weather={weatherData.current}
                      locationName={weatherData.location.name || currentLocation}
                      trust={weatherData.trust}
                    />
                    <HourlySlider hourly={weatherData.hourly} />
                  </div>

                  {/* Conversational Assistant Drawer */}
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

                {/* GIS Map Preview */}
                <GISMapView
                  latitude={latitude}
                  longitude={longitude}
                  locationName={currentLocation}
                />

              </div>
            )}

            {activeTab === 'chat' && (
              <ChatDrawer
                currentLocation={currentLocation}
                latitude={latitude}
                longitude={longitude}
                selectedLanguage={selectedLanguage}
                userRole={userRole}
                isOpenAsFullPage={true}
              />
            )}

            {activeTab === 'map' && (
              <GISMapView
                latitude={latitude}
                longitude={longitude}
                locationName={currentLocation}
              />
            )}

            {activeTab === 'advisories' && (
              <SectorAdvisoryView
                latitude={latitude}
                longitude={longitude}
                locationName={currentLocation}
              />
            )}

            {activeTab === 'climate' && (
              <ClimateTrendsView
                latitude={latitude}
                longitude={longitude}
                locationName={currentLocation}
              />
            )}

            {activeTab === 'admin' && (
              <AdminView />
            )}
          </>
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
