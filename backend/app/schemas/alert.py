from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    GREEN = "green"       # No warning
    YELLOW = "yellow"     # Be updated / Watch
    ORANGE = "orange"     # Be prepared / Alert
    RED = "red"           # Take action / Warning


class AlertType(str, Enum):
    CYCLONE = "cyclone"
    FLOOD = "flood"
    HEAVY_RAINFALL = "heavy_rainfall"
    THUNDERSTORM = "thunderstorm"
    LIGHTNING = "lightning"
    HEATWAVE = "heatwave"
    COLD_WAVE = "cold_wave"
    STRONG_WIND = "strong_wind"
    COASTAL_HAZARD = "coastal_hazard"
    AIR_QUALITY = "air_quality"
    GENERAL = "general"


class WeatherAlert(BaseModel):
    id: str
    headline: str
    description: str
    instruction: str
    severity: AlertSeverity
    alert_type: AlertType
    source: str = "IMD (India Meteorological Department)"
    area_desc: str
    effective_from: datetime
    expires_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    is_active: bool = True
    color_code: str = "#FFCC00"  # Hex color for UI representation


class ActiveAlertsResponse(BaseModel):
    location: str
    count: int
    alerts: List[WeatherAlert]
    highest_severity: AlertSeverity
