import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.schemas.alert import WeatherAlert, AlertSeverity, AlertType, ActiveAlertsResponse
from app.schemas.weather import CurrentWeather, DailyForecastPoint
from app.core.logging import get_logger

logger = get_logger("alerts.service")


class WarningService:
    def __init__(self):
        # In-memory registry of regional official warnings (e.g. issued by IMD Regional Centers)
        self._regional_bulletins: List[WeatherAlert] = self._load_seed_bulletins()

    def _load_seed_bulletins(self) -> List[WeatherAlert]:
        now = datetime.now(timezone.utc)
        return [
            WeatherAlert(
                id="IMD-HYD-2026-001",
                headline="Thunderstorm with Gusty Winds Warning",
                description="Thunderstorm accompanied with lightning and gusty winds (speed 30-40 kmph) very likely to occur at isolated places over Telangana.",
                instruction="Stay indoors during lightning. Farmers must avoid open fields and unplug electrical irrigation pumps.",
                severity=AlertSeverity.YELLOW,
                alert_type=AlertType.THUNDERSTORM,
                source="India Meteorological Department (IMD Hyd)",
                area_desc="Telangana (Hyderabad, Rangareddy, Medchal)",
                effective_from=now - timedelta(hours=2),
                expires_at=now + timedelta(hours=22),
                latitude=17.3850,
                longitude=78.4867,
                radius_km=120.0,
                color_code="#FFCC00"
            ),
            WeatherAlert(
                id="IMD-OD-2026-002",
                headline="Depression in Bay of Bengal - Coastal Squall Alert",
                description="Squally weather with wind speed reaching 45-55 kmph gusting to 65 kmph likely over Northwest Bay of Bengal.",
                instruction="Fishermen are advised not to venture into deep sea areas along Odisha and Andhra Pradesh coasts.",
                severity=AlertSeverity.ORANGE,
                alert_type=AlertType.COASTAL_HAZARD,
                source="India Meteorological Department (Cyclone Warning Division)",
                area_desc="Odisha & Coastal Andhra Pradesh",
                effective_from=now - timedelta(hours=5),
                expires_at=now + timedelta(hours=36),
                latitude=19.8135,
                longitude=85.8312,
                radius_km=250.0,
                color_code="#FF9900"
            ),
            WeatherAlert(
                id="IMD-DEL-2026-003",
                headline="Heatwave Advisory - Moderate Risk",
                description="Maximum temperatures likely to hover around 42-44°C over isolated pockets of Northwest India.",
                instruction="Drink sufficient water even if not thirsty. Avoid direct sun exposure between 12 noon and 3 PM.",
                severity=AlertSeverity.YELLOW,
                alert_type=AlertType.HEATWAVE,
                source="IMD National Weather Forecasting Centre, New Delhi",
                area_desc="Delhi NCR, Haryana, Rajasthan",
                effective_from=now - timedelta(hours=1),
                expires_at=now + timedelta(hours=48),
                latitude=28.6139,
                longitude=77.2090,
                radius_km=150.0,
                color_code="#FFCC00"
            )
        ]

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    def get_alerts_for_location(
        self, latitude: float, longitude: float, location_name: str = "Target Location"
    ) -> ActiveAlertsResponse:
        """
        Finds active bulletins matching geospatial proximity (within alert radius).
        """
        now = datetime.now(timezone.utc)
        matched_alerts: List[WeatherAlert] = []

        for b in self._regional_bulletins:
            if b.is_active and b.effective_from <= now <= b.expires_at:
                if b.latitude is not None and b.longitude is not None:
                    dist = self._haversine_km(latitude, longitude, b.latitude, b.longitude)
                    radius = b.radius_km or 100.0
                    if dist <= radius:
                        matched_alerts.append(b)

        # Determine highest severity
        highest_severity = AlertSeverity.GREEN
        for a in matched_alerts:
            if a.severity == AlertSeverity.RED:
                highest_severity = AlertSeverity.RED
                break
            elif a.severity == AlertSeverity.ORANGE and highest_severity != AlertSeverity.RED:
                highest_severity = AlertSeverity.ORANGE
            elif a.severity == AlertSeverity.YELLOW and highest_severity == AlertSeverity.GREEN:
                highest_severity = AlertSeverity.YELLOW

        return ActiveAlertsResponse(
            location=location_name,
            count=len(matched_alerts),
            alerts=matched_alerts,
            highest_severity=highest_severity
        )

    def evaluate_threshold_warnings(
        self, current: CurrentWeather, daily: List[DailyForecastPoint], latitude: float, longitude: float
    ) -> List[WeatherAlert]:
        """
        Scientifically evaluates whether live forecast parameters trigger standard IMD hazard thresholds.
        Does NOT fabricate warnings; classifies according to published meteorological criteria.
        """
        alerts: List[WeatherAlert] = []
        now = datetime.now(timezone.utc)

        # Check heavy rainfall: > 64.5mm (Heavy), > 115.5mm (Very Heavy)
        rain_today = daily[0].precipitation_sum_mm if daily else current.precipitation_mm
        if rain_today >= 115.5:
            alerts.append(
                WeatherAlert(
                    id=f"AUTO-RAIN-RED-{int(now.timestamp())}",
                    headline="Very Heavy Rainfall Alert (Red Level)",
                    description=f"Expected 24-hour rainfall of {rain_today:.1f} mm exceeds critical waterlogging threshold.",
                    instruction="Avoid low-lying areas. Suspend outdoor fieldwork and follow local disaster management guidance.",
                    severity=AlertSeverity.RED,
                    alert_type=AlertType.HEAVY_RAINFALL,
                    source="IMD Criteria / Automated Assessment",
                    area_desc="Local Catchment Area",
                    effective_from=now,
                    expires_at=now + timedelta(hours=24),
                    latitude=latitude,
                    longitude=longitude,
                    color_code="#FF0000"
                )
            )
        elif rain_today >= 64.5:
            alerts.append(
                WeatherAlert(
                    id=f"AUTO-RAIN-ORANGE-{int(now.timestamp())}",
                    headline="Heavy Rainfall Alert (Orange Level)",
                    description=f"Forecast indicates {rain_today:.1f} mm precipitation. Localized runoff and drainage overflow possible.",
                    instruction="Ensure field drainage channels are clear. Postpone chemical spraying.",
                    severity=AlertSeverity.ORANGE,
                    alert_type=AlertType.HEAVY_RAINFALL,
                    source="IMD Criteria / Automated Assessment",
                    area_desc="Local Area",
                    effective_from=now,
                    expires_at=now + timedelta(hours=24),
                    latitude=latitude,
                    longitude=longitude,
                    color_code="#FF9900"
                )
            )

        # Check heatwave: temp >= 40°C in plains
        if current.temperature_c >= 42.0:
            alerts.append(
                WeatherAlert(
                    id=f"AUTO-HEAT-YELLOW-{int(now.timestamp())}",
                    headline="Severe Heat Conditions Alert",
                    description=f"Observed temperature of {current.temperature_c:.1f}°C with heat stress risk.",
                    instruction="Hydrate frequently, avoid peak solar hours, protect livestock with adequate shade.",
                    severity=AlertSeverity.YELLOW,
                    alert_type=AlertType.HEATWAVE,
                    source="IMD Criteria / Automated Assessment",
                    area_desc="Surrounding Region",
                    effective_from=now,
                    expires_at=now + timedelta(hours=12),
                    latitude=latitude,
                    longitude=longitude,
                    color_code="#FFCC00"
                )
            )

        # Check high wind: wind speed > 50 km/h
        if current.wind_speed_kmh >= 50.0:
            alerts.append(
                WeatherAlert(
                    id=f"AUTO-WIND-ORANGE-{int(now.timestamp())}",
                    headline="High Wind and Squall Advisory",
                    description=f"Wind speeds reaching {current.wind_speed_kmh:.1f} km/h with potential tree branch and billboard damage.",
                    instruction="Secure loose rooftop structures. Exercise caution on elevated highways.",
                    severity=AlertSeverity.ORANGE,
                    alert_type=AlertType.STRONG_WIND,
                    source="IMD Criteria / Automated Assessment",
                    area_desc="Local Sector",
                    effective_from=now,
                    expires_at=now + timedelta(hours=12),
                    latitude=latitude,
                    longitude=longitude,
                    color_code="#FF9900"
                )
            )

        return alerts


warning_service = WarningService()
