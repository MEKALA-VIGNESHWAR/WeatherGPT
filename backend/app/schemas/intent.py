from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    CURRENT_WEATHER = "current_weather"
    FORECAST = "forecast"
    RAINFALL = "rainfall"
    TEMPERATURE = "temperature"
    WIND = "wind"
    SEVERE_WEATHER = "severe_weather"
    WARNING = "warning"
    AGRICULTURE_ADVISORY = "agriculture_advisory"
    TRAVEL_ADVISORY = "travel_advisory"
    AVIATION_ADVISORY = "aviation_advisory"
    MARINE_ADVISORY = "marine_advisory"
    FLOOD_RISK = "flood_risk"
    HEAT_RISK = "heat_risk"
    HISTORICAL_WEATHER = "historical_weather"
    CLIMATE_TREND = "climate_trend"
    COMPARISON = "comparison"
    LOCATION_WEATHER = "location_weather"
    GENERAL_WEATHER_QUESTION = "general_weather_question"


class UserRole(str, Enum):
    CITIZEN = "citizen"
    FARMER = "farmer"
    RESEARCHER = "researcher"
    DISASTER_MANAGER = "disaster_manager"
    AVIATOR = "aviator"
    FISHERMAN = "fisherman"
    ADMIN = "admin"


class TimeRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    relative_day: Optional[str] = "today"  # today, tomorrow, yesterday, this_week, 7_days


class LocationTarget(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class QueryIntent(BaseModel):
    intent: IntentType
    location: Optional[LocationTarget] = None
    time_range: Optional[TimeRange] = None
    parameters: List[str] = Field(default_factory=list)  # rainfall, temp, humidity, wind, alert
    crop: Optional[str] = None  # for agriculture
    travel_mode: Optional[str] = None  # road, flight, sea
    user_type: UserRole = UserRole.CITIZEN
    language: str = "en"
    raw_query: str
    confidence: float = 1.0
