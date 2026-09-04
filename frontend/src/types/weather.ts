export interface LocationInfo {
  name: string;
  latitude: number;
  longitude: number;
  state?: string;
  country?: string;
  elevation_m?: number;
}

export interface CurrentWeather {
  temperature_c: number;
  feels_like_c: number;
  relative_humidity_pct: number;
  wind_speed_kmh: number;
  wind_direction_deg?: number;
  wind_gusts_kmh?: number;
  precipitation_mm: number;
  precipitation_probability_pct?: number;
  surface_pressure_hpa?: number;
  visibility_km?: number;
  uv_index?: number;
  weather_code: number;
  weather_condition: string;
  weather_icon: string;
  sunrise?: string;
  sunset?: string;
}

export interface HourlyForecastPoint {
  time: string;
  temperature_c: number;
  relative_humidity_pct: number;
  precipitation_probability_pct: number;
  precipitation_mm: number;
  wind_speed_kmh: number;
  weather_code: number;
  weather_condition: string;
  weather_icon: string;
}

export interface DailyForecastPoint {
  date: string;
  temperature_max_c: number;
  temperature_min_c: number;
  precipitation_probability_max_pct: number;
  precipitation_sum_mm: number;
  wind_speed_max_kmh: number;
  weather_code: number;
  weather_condition: string;
  weather_icon: string;
  sunrise?: string;
  sunset?: string;
  uv_index_max?: number;
}

export interface TrustMetadata {
  source: string;
  observed_at: string;
  retrieved_at: string;
  data_age_minutes: number;
  source_authority: string;
  confidence: 'high' | 'medium' | 'low' | 'unknown';
  model_agreement: 'high' | 'moderate' | 'low' | 'single_source';
  is_demo_data: boolean;
}

export interface UnifiedWeatherResponse {
  location: LocationInfo;
  current: CurrentWeather;
  hourly: HourlyForecastPoint[];
  daily: DailyForecastPoint[];
  trust: TrustMetadata;
  raw_sources_fused: string[];
}
