import React, { useState } from 'react';
import { MapPin, Sparkles, User, Languages } from './Icons';

interface NavbarProps {
  currentLocation: string;
  onLocationChange: (name: string, lat: number, lon: number) => void;
  selectedLanguage: string;
  onLanguageChange: (lang: string) => void;
  userRole: string;
  onUserRoleChange: (role: string) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isDemoMode?: boolean;
}

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी (Hindi)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml', label: 'മലയാളം (Malayalam)' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
  { code: 'mr', label: 'मराठी (Marathi)' }
];

const PRESET_CITIES = [
  { name: 'Hyderabad', lat: 17.3850, lon: 78.4867, state: 'Telangana' },
  { name: 'Amaravati', lat: 16.5417, lon: 80.5158, state: 'Andhra Pradesh' },
  { name: 'Bengaluru', lat: 12.9716, lon: 77.5946, state: 'Karnataka' },
  { name: 'Chennai', lat: 13.0827, lon: 80.2707, state: 'Tamil Nadu' },
  { name: 'Mumbai', lat: 19.0760, lon: 72.8777, state: 'Maharashtra' },
  { name: 'Delhi', lat: 28.6139, lon: 77.2090, state: 'Delhi' },
  { name: 'Kolkata', lat: 22.5726, lon: 88.3639, state: 'West Bengal' }
];

export const Navbar: React.FC<NavbarProps> = ({
  currentLocation,
  onLocationChange,
  selectedLanguage,
  onLanguageChange,
  userRole,
  onUserRoleChange,
  activeTab,
  setActiveTab,
  isDemoMode = false
}) => {
  const [showLocationDropdown, setShowLocationDropdown] = useState(false);

  const handleDetectGPS = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          onLocationChange('My Location', pos.coords.latitude, pos.coords.longitude);
          setShowLocationDropdown(false);
        },
        () => {
          alert('GPS permission denied. Using default location (Hyderabad).');
        }
      );
    }
  };

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: 'rgba(11, 15, 25, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      padding: '0.75rem 1.5rem'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }} onClick={() => setActiveTab('dashboard')}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
            borderRadius: '10px',
            width: '38px',
            height: '38px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
            boxShadow: '0 0 15px rgba(2, 132, 199, 0.4)'
          }}>
            ☁️
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '4px' }}>
              Weather<span style={{ color: '#38bdf8' }}>GPT</span>
              {isDemoMode && (
                <span style={{
                  fontSize: '0.65rem',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: 'rgba(245, 158, 11, 0.2)',
                  color: '#f59e0b',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  fontWeight: 600,
                  marginLeft: '4px'
                }}>
                  DEMO DATA
                </span>
              )}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 500 }}>
              Meteorological Decision Intelligence
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(17, 24, 39, 0.6)', padding: '4px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)' }}>
          {[
            { id: 'dashboard', label: 'Dashboard' },
            { id: 'chat', label: 'Chat Assistant' },
            { id: 'map', label: 'GIS Map' },
            { id: 'advisories', label: 'Advisories' },
            { id: 'climate', label: 'Climate Trends' },
            { id: 'admin', label: 'Admin' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '0.45rem 0.9rem',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === tab.id ? '#0284c7' : 'transparent',
                color: activeTab === tab.id ? '#ffffff' : '#94a3b8',
                fontWeight: activeTab === tab.id ? 600 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Action Controls: Location, Language, Role */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          
          {/* Location Selector */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowLocationDropdown(!showLocationDropdown)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: 'rgba(30, 41, 59, 0.7)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '0.4rem 0.8rem',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '0.82rem',
                cursor: 'pointer'
              }}
            >
              <MapPin size={15} color="#38bdf8" />
              <span>{currentLocation}</span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>▼</span>
            </button>

            {showLocationDropdown && (
              <div style={{
                position: 'absolute',
                top: '110%',
                right: 0,
                background: '#1e293b',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '10px',
                padding: '0.5rem',
                minWidth: '220px',
                boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                zIndex: 200
              }}>
                <button
                  onClick={handleDetectGPS}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    textAlign: 'left',
                    background: 'rgba(2, 132, 199, 0.2)',
                    border: '1px solid rgba(2, 132, 199, 0.4)',
                    borderRadius: '6px',
                    color: '#38bdf8',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    marginBottom: '0.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  📍 Detect My GPS Location
                </button>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', padding: '0.2rem 0.4rem', fontWeight: 600 }}>
                  INDIAN METEOROLOGICAL CENTERS
                </div>
                {PRESET_CITIES.map((c) => (
                  <div
                    key={c.name}
                    onClick={() => {
                      onLocationChange(c.name, c.lat, c.lon);
                      setShowLocationDropdown(false);
                    }}
                    style={{
                      padding: '0.4rem 0.6rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      color: currentLocation === c.name ? '#38bdf8' : '#e2e8f0',
                      background: currentLocation === c.name ? 'rgba(56, 189, 248, 0.1)' : 'transparent'
                    }}
                  >
                    <span>{c.name}</span>
                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>{c.state}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Language Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '0.25rem 0.5rem', borderRadius: '8px' }}>
            <Languages size={15} color="#94a3b8" />
            <select
              value={selectedLanguage}
              onChange={(e) => onLanguageChange(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#f8fafc',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code} style={{ background: '#1e293b', color: '#fff' }}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          {/* User Role Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '0.25rem 0.5rem', borderRadius: '8px' }}>
            <User size={15} color="#94a3b8" />
            <select
              value={userRole}
              onChange={(e) => onUserRoleChange(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#f8fafc',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="citizen" style={{ background: '#1e293b' }}>Citizen</option>
              <option value="farmer" style={{ background: '#1e293b' }}>Farmer / Agromet</option>
              <option value="disaster_manager" style={{ background: '#1e293b' }}>Disaster Manager</option>
              <option value="researcher" style={{ background: '#1e293b' }}>Researcher</option>
            </select>
          </div>

        </div>

      </div>
    </header>
  );
};
