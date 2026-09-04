from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ModelAgreement(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    SINGLE_SOURCE = "single_source"


class TrustMetadata(BaseModel):
    source: str = Field(..., description="Data provider name (e.g. IMD, Open-Meteo, GFS, WRF, Mock)")
    observed_at: datetime = Field(..., description="Timestamp of observation or model run")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="System retrieval timestamp")
    data_age_minutes: float = Field(0.0, description="Age of data in minutes")
    source_authority: str = Field("official", description="official | global_nwp | local_sensor | simulated")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.HIGH)
    model_agreement: ModelAgreement = Field(ModelAgreement.SINGLE_SOURCE)
    is_demo_data: bool = Field(False, description="Flag indicating if data is mock/sample")


class LocationInfo(BaseModel):
    name: str = Field(..., description="City or district name")
    latitude: float
    longitude: float
    state: Optional[str] = None
    country: Optional[str] = "India"
    elevation_m: Optional[float] = None


class CurrentWeather(BaseModel):
    temperature_c: float
    feels_like_c: float
    relative_humidity_pct: int
    wind_speed_kmh: float
    wind_direction_deg: Optional[int] = None
    wind_gusts_kmh: Optional[float] = None
    precipitation_mm: float = 0.0
    precipitation_probability_pct: Optional[int] = 0
    surface_pressure_hpa: Optional[float] = None
    visibility_km: Optional[float] = None
    uv_index: Optional[float] = None
    weather_code: int = 0
    weather_condition: str = "Clear"
    weather_icon: str = "☀️"
    sunrise: Optional[str] = None
    sunset: Optional[str] = None


class HourlyForecastPoint(BaseModel):
    time: str
    temperature_c: float
    relative_humidity_pct: int
    precipitation_probability_pct: int
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int
    weather_condition: str
    weather_icon: str


class DailyForecastPoint(BaseModel):
    date: str
    temperature_max_c: float
    temperature_min_c: float
    precipitation_probability_max_pct: int
    precipitation_sum_mm: float
    wind_speed_max_kmh: float
    weather_code: int
    weather_condition: str
    weather_icon: str
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    uv_index_max: Optional[float] = None


class UnifiedWeatherResponse(BaseModel):
    location: LocationInfo
    current: CurrentWeather
    hourly: List[HourlyForecastPoint] = []
    daily: List[DailyForecastPoint] = []
    trust: TrustMetadata
    raw_sources_fused: List[str] = []
