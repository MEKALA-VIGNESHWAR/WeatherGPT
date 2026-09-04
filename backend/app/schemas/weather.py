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
    timezone: Optional[str] = "UTC"


class CurrentWeather(BaseModel):
    temperature_c: float
    feels_like_c: float
    relative_humidity_pct: int
    wind_speed_kmh: float
    wind_direction_deg: Optional[int] = None
    wind_gusts_kmh: Optional[float] = None
    precipitation_mm: float = 0.0
    rain_mm: Optional[float] = None
    showers_mm: Optional[float] = None
    snowfall_cm: Optional[float] = None
    cloud_cover_pct: Optional[int] = None
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
    apparent_temperature_c: Optional[float] = None
    relative_humidity_pct: int
    precipitation_probability_pct: int
    precipitation_mm: float
    rain_mm: Optional[float] = None
    cloud_cover_pct: Optional[int] = None
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
    rain_sum_mm: Optional[float] = None
    wind_speed_max_kmh: float
    wind_gusts_max_kmh: Optional[float] = None
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


class DayRainSummary(BaseModel):
    date: str
    day_label: str
    probability_pct: int
    likelihood_label: str
    expected_precipitation_mm: float
    condition: str
    icon: str
    peak_time: str
    temperature_max_c: float
    temperature_min_c: float


class RainAnalysisSummary(BaseModel):
    rain_possible: bool
    highest_probability: int
    highest_probability_date: str
    highest_probability_day_label: str
    highest_probability_time: str
    total_expected_precipitation_mm: float
    best_day_to_avoid_rain: Optional[str] = None
    highest_rain_risk: Optional[str] = None
    umbrella_recommendation: Optional[str] = None


class LocationComparisonItem(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature_c: float
    temperature_max_c: float
    temperature_min_c: float
    condition: str
    icon: str
    rain_probability_pct: int
    precipitation_mm: float
    wind_speed_kmh: float
    humidity_pct: int
    summary_verdict: str


class MultiLocationAnalysis(BaseModel):
    locations: List[LocationComparisonItem] = []
    relational_goal: Optional[str] = None
    comparison_criteria: Optional[str] = None
    activity: Optional[str] = None
    direct_answer: str
    ranking_or_winner: Optional[str] = None
    route_details: Optional[Dict[str, Any]] = None


class WhyExplanation(BaseModel):
    phenomenon: str
    primary_factor: str
    meteorological_drivers: List[str] = []
    observed_parameters: Dict[str, Any] = {}
    verdict: str


class WeatherAnalysis(BaseModel):
    location: str
    period: str
    horizon_days: int
    weather_variable: str
    question_focus: str
    rain_analysis: Optional[RainAnalysisSummary] = None
    daily_breakdown: List[DayRainSummary] = []
    hourly_focus_window: Optional[str] = None
    hourly_focus_details: Optional[Dict[str, Any]] = None
    temperature_comparison: Optional[Dict[str, Any]] = None
    outdoor_recommendation: Optional[Dict[str, Any]] = None
    multi_location: Optional[MultiLocationAnalysis] = None
    why_explanation: Optional[WhyExplanation] = None

