import { UnifiedWeatherResponse } from '../types/weather';
import { ActiveAlertsResponse } from '../types/alert';
import { ChatResponse } from '../types/chat';
import { SectorAdvisoryResponse } from '../types/advisory';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function fetchForecast(lat: number, lon: number, days: number = 7, provider?: string, locationName?: string): Promise<UnifiedWeatherResponse> {
  const locParam = locationName ? `&location_name=${encodeURIComponent(locationName)}` : '';
  const url = `${API_BASE}/weather/forecast?latitude=${lat}&longitude=${lon}&days=${days}${provider ? `&provider=${provider}` : ''}${locParam}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Weather fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchActiveAlerts(lat: number, lon: number, locationName?: string): Promise<ActiveAlertsResponse> {
  const url = `${API_BASE}/alerts/active?latitude=${lat}&longitude=${lon}${locationName ? `&location_name=${encodeURIComponent(locationName)}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Alerts fetch failed: ${res.statusText}`);
  return res.json();
}

export async function sendChatMessage(payload: {
  message: string;
  conversation_id?: string;
  latitude?: number;
  longitude?: number;
  location_name?: string;
  user_role?: string;
  language?: string;
}): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Chat error: ${res.statusText}`);
  return res.json();
}

export async function searchLocations(query: string) {
  const res = await fetch(`${API_BASE}/locations/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return { query, results: [] };
  return res.json();
}

export async function reverseGeocodeLocation(lat: number, lon: number) {
  const res = await fetch(`${API_BASE}/locations/reverse?latitude=${lat}&longitude=${lon}`);
  if (!res.ok) return { name: 'Current Location', latitude: lat, longitude: lon, country: 'India' };
  return res.json();
}

export async function fetchSectorAdvisories(sector: string, lat: number, lon: number, crop: string = 'paddy'): Promise<SectorAdvisoryResponse> {
  const res = await fetch(`${API_BASE}/advisories?sector=${sector}&latitude=${lat}&longitude=${lon}&crop=${crop}`);
  if (!res.ok) throw new Error('Failed to fetch advisories');
  return res.json();
}

export async function fetchClimateTrends(lat: number, lon: number, period: string = '7_days') {
  const res = await fetch(`${API_BASE}/climate/trends?latitude=${lat}&longitude=${lon}&period=${period}`);
  if (!res.ok) throw new Error('Failed to fetch climate trends');
  return res.json();
}

export async function submitChatFeedback(messageId: string, isHelpful: boolean, comment?: string) {
  return fetch(`${API_BASE}/chat/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message_id: messageId, is_helpful: isHelpful, comment })
  });
}

export async function fetchAdminMetrics() {
  const res = await fetch(`${API_BASE}/admin/metrics`);
  if (!res.ok) throw new Error('Failed to fetch admin metrics');
  return res.json();
}
