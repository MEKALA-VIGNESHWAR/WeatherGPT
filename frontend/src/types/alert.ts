export type AlertSeverity = 'green' | 'yellow' | 'orange' | 'red';

export interface WeatherAlert {
  id: string;
  headline: string;
  description: string;
  instruction: string;
  severity: AlertSeverity;
  alert_type: string;
  source: string;
  area_desc: string;
  effective_from: string;
  expires_at: string;
  latitude?: number;
  longitude?: number;
  radius_km?: number;
  is_active: boolean;
  color_code: string;
}

export interface ActiveAlertsResponse {
  location: string;
  count: number;
  alerts: WeatherAlert[];
  highest_severity: AlertSeverity;
}
