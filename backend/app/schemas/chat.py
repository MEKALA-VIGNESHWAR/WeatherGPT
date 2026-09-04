from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.alert import WeatherAlert
from app.schemas.weather import TrustMetadata


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class WeatherSummary(BaseModel):
    temperature_c: Optional[float] = None
    feels_like_c: Optional[float] = None
    condition: Optional[str] = None
    icon: Optional[str] = None
    rainfall_mm: Optional[float] = None
    rain_probability_pct: Optional[int] = None
    wind_kmh: Optional[float] = None
    humidity_pct: Optional[int] = None


class AdvisoryItem(BaseModel):
    sector: str  # agriculture, disaster, travel, citizen
    recommendation: str
    action_type: str  # caution, delay, proceed, alert
    details: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    latitude: Optional[float] = 17.3850  # Default Hyderabad
    longitude: Optional[float] = 78.4867
    location_name: Optional[str] = "Hyderabad"
    user_role: Optional[str] = "citizen"
    language: Optional[str] = "en"  # en, hi, te, ta, kn, ml, bn, mr


class ToolCallTrace(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    execution_time_ms: float
    status: str = "success"


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    location: str
    time_range: str
    weather_summary: WeatherSummary
    risk_level: RiskLevel
    advisories: List[AdvisoryItem] = []
    warnings: List[WeatherAlert] = []
    sources: List[str] = []
    updated_at: str
    confidence: str  # high, medium, low
    trust_metadata: Optional[TrustMetadata] = None
    tools_called: List[ToolCallTrace] = []
    language: str = "en"
    audio_url: Optional[str] = None


class ChatFeedbackRequest(BaseModel):
    message_id: str
    is_helpful: bool
    was_accurate: Optional[bool] = None
    comment: Optional[str] = None
    corrected_info: Optional[str] = None
