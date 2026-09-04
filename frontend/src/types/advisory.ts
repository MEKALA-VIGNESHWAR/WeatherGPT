export interface AdvisoryRecommendation {
  title: string;
  verdict: string;
  icon: string;
  summary: string;
  reasons: string[];
  actionable_steps: string[];
  valid_until: string;
  sector: string;
}

export interface SectorAdvisoryResponse {
  location: string;
  sector: string;
  overall_risk: string;
  recommendations: AdvisoryRecommendation[];
  weather_basis: {
    temperature_c?: number;
    rain_mm?: number;
    rain_prob_pct?: number;
    wind_kmh?: number;
    humidity_pct?: number;
  };
  source: string;
  generated_at: string;
}
