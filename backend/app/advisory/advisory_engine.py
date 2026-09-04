from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.schemas.weather import UnifiedWeatherResponse, DailyForecastPoint
from app.schemas.alert import WeatherAlert, AlertSeverity
from app.schemas.advisory import (
    SectorAdvisoryResponse, AdvisoryRecommendation
)
from app.core.logging import get_logger

logger = get_logger("advisory.engine")


class BaseSectorAdvisory:
    def evaluate(
        self, weather: UnifiedWeatherResponse, alerts: List[WeatherAlert], context: Dict[str, Any]
    ) -> List[AdvisoryRecommendation]:
        raise NotImplementedError


class AgricultureAdvisory(BaseSectorAdvisory):
    """
    Evaluates weather suitability for irrigation, pesticide/fungicide spraying,
    sowing, harvesting, and fertilizer application.
    Supports paddy, cotton, wheat, sugarcane, pulses, vegetables.
    """
    def evaluate(
        self, weather: UnifiedWeatherResponse, alerts: List[WeatherAlert], context: Dict[str, Any]
    ) -> List[AdvisoryRecommendation]:
        recs: List[AdvisoryRecommendation] = []
        curr = weather.current
        daily = weather.daily
        tomorrow = daily[1] if len(daily) > 1 else daily[0] if daily else None

        crop = context.get("crop", "paddy/general crops")
        tomorrow_rain_prob = tomorrow.precipitation_probability_max_pct if tomorrow else curr.precipitation_probability_pct or 0
        tomorrow_rain_mm = tomorrow.precipitation_sum_mm if tomorrow else curr.precipitation_mm

        # 1. Irrigation Advisory
        if tomorrow_rain_prob >= 50 or tomorrow_rain_mm >= 5.0:
            recs.append(
                AdvisoryRecommendation(
                    title="Irrigation Recommendation",
                    verdict="DELAY_IRRIGATION",
                    icon="🌧️",
                    summary=f"Delay irrigation for {crop}. Significant precipitation is forecast.",
                    reasons=[
                        f"Expected rainfall: {tomorrow_rain_mm:.1f} mm with {tomorrow_rain_prob}% probability.",
                        "Irrigating now would cause waterlogging, nutrient leaching, and waste water/electricity."
                    ],
                    actionable_steps=[
                        "Hold off on turning on irrigation pumps tomorrow morning.",
                        "Inspect drainage bunds to ensure excess rainwater can drain freely.",
                        "Re-evaluate soil moisture after rainfall subsides."
                    ],
                    valid_until=tomorrow.date if tomorrow else "Tomorrow evening",
                    sector="agriculture"
                )
            )
        else:
            recs.append(
                AdvisoryRecommendation(
                    title="Irrigation Recommendation",
                    verdict="SAFE_TO_IRRIGATE",
                    icon="💧",
                    summary=f"Favorable conditions for scheduled irrigation of {crop}.",
                    reasons=[
                        f"Rainfall probability is low ({tomorrow_rain_prob}%).",
                        f"Daytime high temperatures will reach {tomorrow.temperature_max_c if tomorrow else curr.temperature_c}°C."
                    ],
                    actionable_steps=[
                        "Proceed with scheduled light or drip irrigation.",
                        "Prefer early morning or late afternoon irrigation to minimize evaporative losses."
                    ],
                    valid_until=tomorrow.date if tomorrow else "Tomorrow evening",
                    sector="agriculture"
                )
            )

        # 2. Pesticide / Fertilizer Spraying Advisory
        wind_speed = curr.wind_speed_kmh
        if tomorrow_rain_prob >= 40 or tomorrow_rain_mm >= 2.0:
            recs.append(
                AdvisoryRecommendation(
                    title="Pesticide & Foliar Spray Advisory",
                    verdict="NOT_RECOMMENDED",
                    icon="🚫",
                    summary="Postpone pesticide, fungicide, or herbicide spraying.",
                    reasons=[
                        f"Forecasted rain ({tomorrow_rain_mm:.1f} mm) will wash off chemical applications before absorption.",
                        "Reduces chemical efficacy and leads to environmental run-off."
                    ],
                    actionable_steps=[
                        "Postpone foliar applications until at least 24 hours of dry weather is forecast.",
                        "Check local IMD radar/nowcast before scheduling spraying."
                    ],
                    valid_until=tomorrow.date if tomorrow else "Tomorrow evening",
                    sector="agriculture"
                )
            )
        elif wind_speed > 20.0:
            recs.append(
                AdvisoryRecommendation(
                    title="Pesticide Spraying Advisory",
                    verdict="CAUTION_DRIFT",
                    icon="💨",
                    summary="High wind drift hazard during chemical spraying.",
                    reasons=[
                        f"Wind speeds of {wind_speed:.1f} km/h will cause severe droplet drift into non-target areas."
                    ],
                    actionable_steps=[
                        "Avoid spraying until winds subside below 15 km/h, preferably early morning."
                    ],
                    valid_until="Today evening",
                    sector="agriculture"
                )
            )
        else:
            recs.append(
                AdvisoryRecommendation(
                    title="Pesticide Spraying Advisory",
                    verdict="FAVORABLE",
                    icon="🌾",
                    summary="Conditions are suitable for protective or foliar spraying.",
                    reasons=[
                        "Calm wind conditions and dry weather forecast over the next 24 hours."
                    ],
                    actionable_steps=[
                        "Use recommended personal protective equipment (PPE).",
                        "Complete applications before midday peak heat."
                    ],
                    valid_until=tomorrow.date if tomorrow else "Tomorrow evening",
                    sector="agriculture"
                )
            )

        return recs


class DisasterAdvisory(BaseSectorAdvisory):
    """
    Evaluates extreme event preparedness: Floods, Cyclone tracks, Heatwave protocols, Severe Thunderstorms.
    """
    def evaluate(
        self, weather: UnifiedWeatherResponse, alerts: List[WeatherAlert], context: Dict[str, Any]
    ) -> List[AdvisoryRecommendation]:
        recs: List[AdvisoryRecommendation] = []
        curr = weather.current

        # Check official alerts first
        red_alerts = [a for a in alerts if a.severity == AlertSeverity.RED]
        orange_alerts = [a for a in alerts if a.severity == AlertSeverity.ORANGE]

        if red_alerts:
            a = red_alerts[0]
            recs.append(
                AdvisoryRecommendation(
                    title=f"CRITICAL DISASTER ALERT: {a.headline}",
                    verdict="HIGH_HAZARD",
                    icon="🚨",
                    summary=a.description,
                    reasons=[
                        f"Official Alert Level: RED ({a.source}).",
                        a.instruction
                    ],
                    actionable_steps=[
                        "Activate district/local emergency response protocols.",
                        "Evacuate vulnerable riverbank and low-lying settlements if instructed.",
                        "Charge emergency battery packs, phones, and store 48 hours of potable water."
                    ],
                    valid_until=a.expires_at.strftime("%Y-%m-%d %H:%M UTC"),
                    sector="disaster"
                )
            )
        elif orange_alerts:
            a = orange_alerts[0]
            recs.append(
                AdvisoryRecommendation(
                    title=f"Disaster Preparedness Alert: {a.headline}",
                    verdict="PREPAREDNESS_REQUIRED",
                    icon="⚠️",
                    summary=a.description,
                    reasons=[
                        f"Official Alert Level: ORANGE ({a.source}).",
                        a.instruction
                    ],
                    actionable_steps=[
                        "Inspect municipal storm water drains and clear debris.",
                        "Keep emergency medical kits and flashlights ready.",
                        "Monitor hourly weather bulletins."
                    ],
                    valid_until=a.expires_at.strftime("%Y-%m-%d %H:%M UTC"),
                    sector="disaster"
                )
            )
        elif curr.temperature_c >= 41.0:
            recs.append(
                AdvisoryRecommendation(
                    title="Heat Action Plan Warning",
                    verdict="HEATWAVE_CAUTION",
                    icon="☀️",
                    summary="Extreme heat stress levels observed.",
                    reasons=[
                        f"Temperature reached {curr.temperature_c:.1f}°C (Feels like {curr.feels_like_c:.1f}°C)."
                    ],
                    actionable_steps=[
                        "Maintain cool hydration centers and oral rehydration salt (ORS) supplies.",
                        "Suspend heavy outdoor labor between 12:00 PM and 3:30 PM."
                    ],
                    valid_until="Today 18:00",
                    sector="disaster"
                )
            )
        else:
            recs.append(
                AdvisoryRecommendation(
                    title="Disaster Threat Assessment",
                    verdict="NORMAL",
                    icon="🛡️",
                    summary="No immediate catastrophic weather hazards detected.",
                    reasons=["All meteorological parameters are within seasonal tolerance levels."],
                    actionable_steps=["Maintain standard municipal and emergency standby readiness."],
                    valid_until="Next 24 hours",
                    sector="disaster"
                )
            )

        return recs


class CitizenAdvisory(BaseSectorAdvisory):
    """
    Daily life, commute safety, outdoor sports, school travel, and health comfort.
    """
    def evaluate(
        self, weather: UnifiedWeatherResponse, alerts: List[WeatherAlert], context: Dict[str, Any]
    ) -> List[AdvisoryRecommendation]:
        recs: List[AdvisoryRecommendation] = []
        curr = weather.current
        daily = weather.daily
        rain_prob = curr.precipitation_probability_pct or (daily[0].precipitation_probability_max_pct if daily else 0)

        # Commute & Travel
        if rain_prob > 60 or curr.precipitation_mm > 1.0:
            recs.append(
                AdvisoryRecommendation(
                    title="Commute & Road Safety",
                    verdict="ALLOW_EXTRA_TRAVEL_TIME",
                    icon="🚗",
                    summary="Wet roads and potential waterlogging on city routes.",
                    reasons=[
                        f"Rain probability: {rain_prob}%. Possible slick asphalt and reduced visibility."
                    ],
                    actionable_steps=[
                        "Carry an umbrella or rain gear.",
                        "Maintain increased braking distance and avoid known waterlogged underpasses."
                    ],
                    valid_until="Today",
                    sector="citizen"
                )
            )
        else:
            recs.append(
                AdvisoryRecommendation(
                    title="Commute & Road Safety",
                    verdict="CLEAR_TRAVEL",
                    icon="🚲",
                    summary="Favorable conditions for commuting and outdoor activities.",
                    reasons=["Dry roads and good horizontal visibility."],
                    actionable_steps=["Standard commute precautions."],
                    valid_until="Today",
                    sector="citizen"
                )
            )

        return recs


class MarineAdvisory(BaseSectorAdvisory):
    """
    Coastal safety, fishermen advisory, sea-state and wind gust analysis.
    """
    def evaluate(
        self, weather: UnifiedWeatherResponse, alerts: List[WeatherAlert], context: Dict[str, Any]
    ) -> List[AdvisoryRecommendation]:
        curr = weather.current
        wind = curr.wind_speed_kmh

        if wind >= 45.0:
            return [
                AdvisoryRecommendation(
                    title="Fishermen Sea-Venture Warning",
                    verdict="DANGER_DO_NOT_VENTURE",
                    icon="🌊",
                    summary=f"Rough to very rough sea conditions with wind speeds of {wind:.1f} km/h.",
                    reasons=["Squally winds create dangerous wave heights exceeding 3.5 meters."],
                    actionable_steps=[
                        "Fishermen are strictly advised not to venture into deep sea or coastal waters.",
                        "Boats docked at coastal jetties must be securely moored."
                    ],
                    valid_until="Next 24 hours",
                    sector="marine"
                )
            ]
        else:
            return [
                AdvisoryRecommendation(
                    title="Coastal Marine Conditions",
                    verdict="MODERATE_SEA",
                    icon="⛵",
                    summary="Moderate wind speeds and normal tidal activity.",
                    reasons=[f"Wind speed {wind:.1f} km/h is within safe sailing limits."],
                    actionable_steps=["Maintain standard radio check-in before setting sail."],
                    valid_until="Next 24 hours",
                    sector="marine"
                )
            ]


class AviationAdvisory(BaseSectorAdvisory):
    """
    Visibility, cross-wind, and convective thunderstorm hazards for general aviation and drones.
    """
    def evaluate(
        self, weather: UnifiedWeatherResponse, alerts: List[WeatherAlert], context: Dict[str, Any]
    ) -> List[AdvisoryRecommendation]:
        curr = weather.current
        vis = curr.visibility_km or 10.0
        gusts = curr.wind_gusts_kmh or curr.wind_speed_kmh

        if vis < 3.0 or gusts > 40.0:
            return [
                AdvisoryRecommendation(
                    title="Aviation / Drone Flight Advisory",
                    verdict="MARGINAL_VFR_OR_IFR",
                    icon="✈️",
                    summary="Adverse atmospheric conditions for visual flight rules (VFR) and UAV operations.",
                    reasons=[f"Visibility {vis:.1f} km and gusts up to {gusts:.1f} km/h."],
                    actionable_steps=[
                        "Ground small drone/UAV flights.",
                        "Verify airport METAR/TAF reports before departure."
                    ],
                    valid_until="Next 6 hours",
                    sector="aviation"
                )
            ]
        else:
            return [
                AdvisoryRecommendation(
                    title="Aviation / Flight Conditions",
                    verdict="VFR_FAVORABLE",
                    icon="🛫",
                    summary="Clear visual conditions and acceptable cross-wind parameters.",
                    reasons=[f"Visibility {vis:.1f} km, calm to moderate winds."],
                    actionable_steps=["Normal flight planning."],
                    valid_until="Next 12 hours",
                    sector="aviation"
                )
            ]


class AdvisoryEngine:
    def __init__(self):
        self.modules = {
            "agriculture": AgricultureAdvisory(),
            "disaster": DisasterAdvisory(),
            "citizen": CitizenAdvisory(),
            "marine": MarineAdvisory(),
            "aviation": AviationAdvisory()
        }

    def generate_advisory(
        self,
        sector: str,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Optional[Dict[str, Any]] = None
    ) -> SectorAdvisoryResponse:
        ctx = context or {}
        mod = self.modules.get(sector.lower(), self.modules["citizen"])
        recs = mod.evaluate(weather, alerts, ctx)

        # Determine overall risk
        overall_risk = "LOW"
        for r in recs:
            if "HAZARD" in r.verdict or "CRITICAL" in r.verdict or "DANGER" in r.verdict:
                overall_risk = "CRITICAL"
                break
            elif "NOT_RECOMMENDED" in r.verdict or "CAUTION" in r.verdict or "PREPAREDNESS" in r.verdict:
                overall_risk = "MEDIUM"

        return SectorAdvisoryResponse(
            location=weather.location.name,
            sector=sector.lower(),
            overall_risk=overall_risk,
            recommendations=recs,
            weather_basis={
                "temperature_c": weather.current.temperature_c,
                "rain_mm": weather.current.precipitation_mm,
                "rain_prob_pct": weather.current.precipitation_probability_pct,
                "wind_kmh": weather.current.wind_speed_kmh,
                "humidity_pct": weather.current.relative_humidity_pct
            },
            source=weather.trust.source,
            generated_at=datetime.now(timezone.utc).isoformat()
        )


advisory_engine = AdvisoryEngine()
