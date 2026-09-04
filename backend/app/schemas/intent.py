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
    GENERAL_QUESTION = "general_question"


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
    relative_day: Optional[str] = "today"  # today, tonight, tomorrow, tomorrow_evening, weekend, next_n_days
    target_hour: Optional[int] = None  # 0 to 23 if user asks for specific time like 6 PM
    hour_start: Optional[int] = None   # e.g. 17 for evening
    hour_end: Optional[int] = None     # e.g. 21 for evening
    horizon_days: int = 1              # 1 for today/tomorrow, 4 for next 4 days, 7 for weekly
    day_offset: int = 0                # 0 for today, 1 for tomorrow


class LocationTarget(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    state: Optional[str] = None
    country: Optional[str] = None


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
    candidate_location: Optional[str] = None
    locations: List[LocationTarget] = Field(default_factory=list)
    candidate_locations: List[str] = Field(default_factory=list)
    origin_location: Optional[LocationTarget] = None
    destination_location: Optional[LocationTarget] = None
    comparison_criteria: Optional[str] = None  # temperature, rain, wind, comfort, overall
    relational_goal: Optional[str] = None      # compare, best, worst, highest, lowest, avoid, why, recommendation
    activity: Optional[str] = None             # outdoor, driving, sports, drone, farming
    location_unresolved: bool = False
    raw_location_query: Optional[str] = None
    weather_variable: str = "general"  # rain, temperature, humidity, wind, umbrella, outdoor, general
    question_focus: str = "general"    # rain_possibility, peak_rain_time, best_outdoor_day, carry_umbrella, compare_days, compare_locations, temperature_forecast, general_weather
