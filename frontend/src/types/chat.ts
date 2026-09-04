import { WeatherAlert } from './alert';
import { TrustMetadata } from './weather';

export interface WeatherSummary {
  temperature_c?: number;
  feels_like_c?: number;
  condition?: string;
  icon?: string;
  rainfall_mm?: number;
  rain_probability_pct?: number;
  wind_kmh?: number;
  humidity_pct?: number;
}

export interface AdvisoryItem {
  sector: string;
  recommendation: string;
  action_type: string;
  details?: string;
}

export interface ToolCallTrace {
  tool_name: string;
  arguments: Record<string, any>;
  execution_time_ms: number;
  status: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  location: string;
  time_range: string;
  weather_summary: WeatherSummary;
  risk_level: 'low' | 'medium' | 'high' | 'critical' | 'unknown';
  advisories: AdvisoryItem[];
  warnings: WeatherAlert[];
  sources: string[];
  updated_at: string;
  confidence: string;
  trust_metadata?: TrustMetadata;
  tools_called: ToolCallTrace[];
  language: string;
  audio_url?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  data?: ChatResponse;
  timestamp: string;
  isStreaming?: boolean;
}
