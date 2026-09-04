export interface HorizonBreakdownItem {
  day: string;
  date: string;
  rain_probability_pct: number;
  rain_sum_mm: number;
  wind_max_kmh: number;
  irrigation_verdict: string;
  spraying_verdict: string;
  condition: string;
}

export interface AdvisoryRecommendation {
  sector: string;
  location: string;
  crop?: string;
  title: string;
  recommendation: string; // DELAY_IRRIGATION, IRRIGATE, POSTPONE, RECOMMENDED, etc.
  verdict?: string; // backward-compat alias
  icon: string;
  risk_level: string; // LOW, MEDIUM, HIGH, CRITICAL
  risk_score: number;
  risk_factors: string[];
  weather_trigger?: Record<string, any>;
  basis: string[];
  reasons?: string[]; // backward-compat alias
  recommended_actions: string[];
  actionable_steps?: string[]; // backward-compat alias
  avoid_actions: string[];
  valid_from: string;
  valid_until: string;
  sources: string[];
  confidence: string;
  limitations: string[];
  horizon_breakdown?: HorizonBreakdownItem[];
}

export interface SectorAdvisoryResponse {
  location: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
  sector: string;
  overall_risk: string;
  overall_risk_score?: number;
  advisories: AdvisoryRecommendation[];
  recommendations: AdvisoryRecommendation[]; // backward-compat alias
  weather_basis: {
    temperature_c?: number;
    rain_mm?: number;
    rain_prob_pct?: number;
    wind_kmh?: number;
    humidity_pct?: number;
  };
  sources: string[];
  source?: string; // backward-compat alias
  generated_at: string;
  official_alerts?: any[];
}
