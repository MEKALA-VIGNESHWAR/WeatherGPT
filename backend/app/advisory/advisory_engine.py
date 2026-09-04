from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.schemas.weather import UnifiedWeatherResponse, DailyForecastPoint, CurrentWeather
from app.schemas.alert import WeatherAlert, AlertSeverity
from app.schemas.advisory import (
    SectorAdvisoryResponse, SectorAdvisoryItem, AdvisoryRecommendation
)
from app.advisory.config import get_crop_profile, CropRuleConfig
from app.advisory.risk_engine import risk_engine
from app.core.logging import get_logger

logger = get_logger("advisory.engine")


class BaseSectorModule:
    def evaluate(
        self,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Dict[str, Any]
    ) -> List[SectorAdvisoryItem]:
        raise NotImplementedError


class AgricultureSectorModule(BaseSectorModule):
    """
    Dynamic, data-driven agronomic decision engine for crop management.
    Evaluates irrigation, chemical/foliar spraying, and crop weather risks
    against configurable crop profiles (Paddy, Cotton, Wheat, Sugarcane, Chilli).
    """

    def evaluate(
        self,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Dict[str, Any]
    ) -> List[SectorAdvisoryItem]:
        advisories: List[SectorAdvisoryItem] = []
        curr = weather.current
        daily = weather.daily
        tomorrow = daily[1] if len(daily) > 1 else (daily[0] if daily else None)
        crop_query = context.get("crop", "paddy")
        crop_profile = get_crop_profile(crop_query)
        horizon_days = context.get("horizon_days", 1)

        # Dynamic local time strings
        now_utc = datetime.now(timezone.utc)
        valid_from_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
        valid_until_str = (now_utc + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M UTC")
        if tomorrow and tomorrow.date:
            valid_until_str = f"{tomorrow.date} 23:59 (Forecast window)"

        # Target forecast data for evaluation
        eval_point = tomorrow if tomorrow else (daily[0] if daily else None)
        rain_prob = (eval_point.precipitation_probability_max_pct if (eval_point and eval_point.precipitation_probability_max_pct is not None) else (curr.precipitation_probability_pct or 0)) or 0
        rain_mm = (eval_point.precipitation_sum_mm if (eval_point and eval_point.precipitation_sum_mm is not None) else (curr.precipitation_mm or 0.0)) or 0.0
        temp_max = (eval_point.temperature_max_c if (eval_point and eval_point.temperature_max_c is not None) else (curr.temperature_c or 28.0)) or 28.0
        wind_speed = (eval_point.wind_speed_max_kmh if (eval_point and eval_point.wind_speed_max_kmh is not None) else (curr.wind_speed_kmh or 0.0)) or 0.0
        wind_gusts = (eval_point.wind_gusts_max_kmh if (eval_point and eval_point.wind_gusts_max_kmh is not None) else (curr.wind_gusts_kmh or wind_speed)) or wind_speed
        humidity = curr.relative_humidity_pct or 50

        # -------------------------------------------------------------
        # 1. IRRIGATION ADVISORY (Dynamic Crop Rules)
        # -------------------------------------------------------------
        irrigation_score, irrigation_risk, irr_factors = risk_engine.calculate_risk(
            current=curr, daily=eval_point, alerts=alerts, sector="agriculture", crop=crop_profile.crop_name
        )

        irr_trigger = {
            "crop": crop_profile.display_name,
            "rain_probability_pct": rain_prob,
            "expected_precipitation_mm": round(rain_mm, 1),
            "forecast_temperature_max_c": temp_max,
            "rule_threshold_prob": crop_profile.irrigation_rain_prob_delay_pct,
            "rule_threshold_mm": crop_profile.irrigation_rain_mm_delay
        }

        irr_basis = []
        irr_recs = []
        irr_avoids = []

        if rain_prob >= crop_profile.irrigation_rain_prob_delay_pct or rain_mm >= crop_profile.irrigation_rain_mm_delay:
            irr_verdict = "DELAY_IRRIGATION"
            irr_icon = "🌧️"
            irr_title = f"{crop_profile.display_name} Irrigation Advisory"
            irr_basis.append(
                f"Precipitation probability is {rain_prob}% with ~{rain_mm:.1f} mm expected rainfall during the forecast window."
            )
            irr_basis.append(
                f"{crop_profile.display_name} threshold for delaying irrigation is {crop_profile.irrigation_rain_prob_delay_pct}% or {crop_profile.irrigation_rain_mm_delay:.1f} mm."
            )
            if rain_mm >= crop_profile.irrigation_heavy_rain_drainage_mm:
                irr_basis.append(
                    f"Expected precipitation ({rain_mm:.1f} mm) exceeds drainage threshold ({crop_profile.irrigation_heavy_rain_drainage_mm:.1f} mm), posing waterlogging hazards."
                )
                irr_recs.append("Inspect field drainage bunds to ensure free outflow of excess storm water.")
                irr_avoids.append("Do not allow standing water to accumulate beyond crop tolerance limits.")

            irr_recs.extend([
                "Consider delaying planned irrigation pump runs until post-rainfall moisture is verified.",
                "Reassess root-zone soil moisture after the rain event before resuming irrigation schedules."
            ])
            irr_avoids.extend([
                "Avoid unnecessary pumping to prevent waterlogging, soil compaction, and nutrient leaching.",
                "Avoid applying water-soluble fertilizers immediately prior to the rainfall window."
            ])
        elif rain_prob >= 30:
            irr_verdict = "MONITOR_SOIL_MOISTURE"
            irr_icon = "💧"
            irr_title = f"{crop_profile.display_name} Irrigation Advisory"
            irr_basis.append(
                f"Moderate precipitation probability ({rain_prob}%) with low expected accumulation ({rain_mm:.1f} mm)."
            )
            irr_basis.append(
                "Rainfall may only partially meet evapotranspiration demands."
            )
            irr_recs.extend([
                "Check subsurface soil moisture at 10-15 cm depth before deciding to irrigate.",
                "Apply light deficit irrigation if soil moisture is inadequate for current vegetative stage."
            ])
            irr_avoids.append("Avoid heavy flood irrigation that may saturate the root zone if sudden showers occur.")
        else:
            irr_verdict = "IRRIGATE"
            irr_icon = "💧"
            irr_title = f"{crop_profile.display_name} Irrigation Advisory"
            irr_basis.append(
                f"Low precipitation probability ({rain_prob}%) and dry weather forecast over the upcoming period."
            )
            irr_basis.append(
                f"Maximum temperatures reach {temp_max:.1f}°C, sustaining regular crop water demand."
            )
            irr_recs.extend([
                "Proceed with scheduled irrigation as per crop growth stage requirements.",
                "Prefer early morning or evening irrigation to minimize evaporative losses."
            ])
            irr_avoids.append("Avoid midday irrigation under peak solar radiation to prevent leaf scald and rapid evaporation.")

        advisories.append(
            SectorAdvisoryItem(
                sector="agriculture",
                location=weather.location.name,
                crop=crop_profile.crop_name,
                title=irr_title,
                recommendation=irr_verdict,
                icon=irr_icon,
                risk_level=irrigation_risk,
                risk_score=irrigation_score,
                risk_factors=irr_factors,
                weather_trigger=irr_trigger,
                basis=irr_basis,
                recommended_actions=irr_recs,
                avoid_actions=irr_avoids,
                valid_from=valid_from_str,
                valid_until=valid_until_str,
                sources=["Open-Meteo forecast"],
                confidence="Based on current forecast data",
                limitations=[
                    "Recommendation is based on atmospheric forecast data; local soil texture, crop age, and irrigation method must be considered.",
                    "Verify field tensiometer or soil moisture feel before operating heavy pumps."
                ]
            )
        )

        # -------------------------------------------------------------
        # 2. PESTICIDE / FOLIAR SPRAY ADVISORY (Dynamic Crop Rules)
        # -------------------------------------------------------------
        spray_basis = []
        spray_recs = []
        spray_avoids = []
        spray_trigger = {
            "crop": crop_profile.display_name,
            "rain_probability_pct": rain_prob,
            "expected_precipitation_mm": round(rain_mm, 1),
            "wind_speed_kmh": round(wind_speed, 1),
            "wind_gusts_kmh": round(wind_gusts, 1),
            "relative_humidity_pct": humidity,
            "rule_max_wind_kmh": crop_profile.spray_wind_speed_max_kmh,
            "rule_max_rain_prob": crop_profile.spray_rain_prob_postpone_pct
        }

        # Check conditions
        is_rain_risk = (rain_prob >= crop_profile.spray_rain_prob_postpone_pct or rain_mm >= crop_profile.spray_rain_mm_postpone)
        is_wind_risk = (wind_speed > crop_profile.spray_wind_speed_max_kmh or wind_gusts > crop_profile.spray_wind_speed_max_kmh + 5.0)
        is_drift_caution = (wind_speed > crop_profile.spray_wind_drift_caution_kmh)

        if is_rain_risk and is_wind_risk:
            spray_verdict = "NOT_RECOMMENDED"
            spray_icon = "🚫"
            spray_title = f"{crop_profile.display_name} Chemical Spray Advisory"
            spray_basis.append(
                f"Unfavorable conditions: Rain chance ({rain_prob}%) and squally winds ({wind_speed:.1f} km/h, gusts {wind_gusts:.1f} km/h)."
            )
            spray_basis.append(
                "Rainfall causes chemical wash-off, and high winds create severe droplet drift into non-target areas."
            )
            spray_recs.append("Postpone all foliar chemical applications until at least a 24-hour dry, calm window opens.")
            spray_avoids.extend([
                "Do not spray systemic or contact pesticides under rain threat.",
                "Never operate motorized mist blowers in gusty winds."
            ])
        elif is_rain_risk:
            spray_verdict = "POSTPONE"
            spray_icon = "🌧️"
            spray_title = f"{crop_profile.display_name} Chemical Spray Advisory"
            spray_basis.append(
                f"Rain probability is {rain_prob}% with ~{rain_mm:.1f} mm precipitation expected."
            )
            spray_basis.append(
                f"Foliar chemical applications for {crop_profile.display_name} require a rain-free window of at least {crop_profile.spray_dry_window_hours_needed} hours for proper absorption."
            )
            spray_recs.extend([
                "Postpone foliar sprays until clear weather is forecast.",
                "If emergency pest intervention is essential, use rain-fast formulations with certified stickers/adjuvants if label permits."
            ])
            spray_avoids.append("Avoid applying foliar nutrients or expensive fungicides immediately prior to rain.")
        elif is_wind_risk or is_drift_caution:
            spray_verdict = "CAUTION_DRIFT"
            spray_icon = "💨"
            spray_title = f"{crop_profile.display_name} Chemical Spray Advisory"
            spray_basis.append(
                f"Wind speed ({wind_speed:.1f} km/h) exceeds safe droplet retention thresholds ({crop_profile.spray_wind_drift_caution_kmh} km/h)."
            )
            spray_recs.extend([
                "Schedule spraying operations during early morning calm hours (06:00-09:00 AM).",
                "Utilize low-drift anti-drift nozzles and keep boom height close to the canopy."
            ])
            spray_avoids.append("Avoid spraying during peak daytime gust periods.")
        else:
            spray_verdict = "RECOMMENDED"
            spray_icon = "🌾"
            spray_title = f"{crop_profile.display_name} Chemical Spray Advisory"
            spray_basis.append(
                f"Calm winds ({wind_speed:.1f} km/h) and dry weather forecast ({rain_prob}% rain probability)."
            )
            spray_basis.append(
                "Atmospheric conditions provide an adequate absorption window."
            )
            spray_recs.extend([
                "Conditions are suitable for protective or foliar chemical application.",
                "Wear recommended personal protective equipment (PPE) and strictly follow product label dosages."
            ])
            spray_avoids.append("Avoid spraying during peak midday heat (>35°C) to prevent droplet evaporation.")

        # Check prolonged humidity disease risk
        if humidity >= crop_profile.prolonged_humidity_risk_pct and rain_prob >= 30:
            spray_basis.append(
                f"High relative humidity ({humidity}%) combined with warm damp weather increases fungal disease susceptibility."
            )
            spray_recs.append(f"Scout {crop_profile.display_name} fields for early symptoms of fungal leaf spots or blight.")

        advisories.append(
            SectorAdvisoryItem(
                sector="agriculture",
                location=weather.location.name,
                crop=crop_profile.crop_name,
                title=spray_title,
                recommendation=spray_verdict,
                icon=spray_icon,
                risk_level=irrigation_risk,
                risk_score=irrigation_score,
                risk_factors=irr_factors,
                weather_trigger=spray_trigger,
                basis=spray_basis,
                recommended_actions=spray_recs,
                avoid_actions=spray_avoids,
                valid_from=valid_from_str,
                valid_until=valid_until_str,
                sources=["Open-Meteo forecast"],
                confidence="Based on current forecast data",
                limitations=[
                    "Strictly follow statutory chemical label requirements, pre-harvest intervals (PHI), and safety guidelines.",
                    "Local wind gusts in open fields can vary from regional automated weather station readings."
                ]
            )
        )

        # -------------------------------------------------------------
        # 3. MULTI-DAY HORIZON BREAKDOWN (If user asked for multi-day)
        # -------------------------------------------------------------
        if horizon_days >= 2 and daily:
            days_breakdown = []
            for i, d in enumerate(daily[:min(4, len(daily))]):
                day_label = f"Day {i+1} ({d.date})" if i > 0 else f"Today ({d.date})"
                d_prob = (d.precipitation_probability_max_pct if d.precipitation_probability_max_pct is not None else 0) or 0
                d_rain = (d.precipitation_sum_mm if d.precipitation_sum_mm is not None else 0.0) or 0.0
                d_wind = (d.wind_speed_max_kmh if d.wind_speed_max_kmh is not None else 0.0) or 0.0

                d_irr = "DELAY" if (d_prob >= crop_profile.irrigation_rain_prob_delay_pct or d_rain >= crop_profile.irrigation_rain_mm_delay) else "POSSIBLE"
                d_spray = "NOT_RECOMMENDED" if (d_prob >= crop_profile.spray_rain_prob_postpone_pct or d_rain >= crop_profile.spray_rain_mm_postpone or d_wind > crop_profile.spray_wind_speed_max_kmh) else "FAVORABLE"

                days_breakdown.append({
                    "day": day_label,
                    "date": d.date,
                    "rain_probability_pct": d_prob,
                    "rain_sum_mm": round(d_rain, 1),
                    "wind_max_kmh": round(d_wind, 1),
                    "irrigation_verdict": d_irr,
                    "spraying_verdict": d_spray,
                    "condition": d.weather_condition
                })

            # Append multi-day summary item
            advisories[0].horizon_breakdown = days_breakdown

        return advisories


class DisasterSectorModule(BaseSectorModule):
    """
    Evaluates extreme event preparedness: Floods, Squall winds, Heatwave protocols, Severe Convection.
    Strictly separates verified official government warnings from meteorological forecast indicators.
    """

    def evaluate(
        self,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Dict[str, Any]
    ) -> List[SectorAdvisoryItem]:
        curr = weather.current
        daily = weather.daily
        tomorrow = daily[1] if len(daily) > 1 else (daily[0] if daily else None)

        now_utc = datetime.now(timezone.utc)
        valid_from_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
        valid_until_str = (now_utc + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M UTC")

        score, level, factors = risk_engine.calculate_risk(
            current=curr, daily=tomorrow, alerts=alerts, sector="disaster"
        )

        red_alerts = [a for a in alerts if a.severity == AlertSeverity.RED]
        orange_alerts = [a for a in alerts if a.severity == AlertSeverity.ORANGE]

        trigger = {
            "temperature_c": curr.temperature_c,
            "wind_speed_kmh": curr.wind_speed_kmh,
            "wind_gusts_kmh": curr.wind_gusts_kmh or curr.wind_speed_kmh,
            "precipitation_mm": curr.precipitation_mm,
            "weather_code": curr.weather_code,
            "official_red_alerts": len(red_alerts),
            "official_orange_alerts": len(orange_alerts)
        }

        basis = []
        recs = []
        avoids = []

        if red_alerts:
            a = red_alerts[0]
            verdict = "CRITICAL_HAZARD"
            icon = "🚨"
            title = f"OFFICIAL WARNING: {a.headline}"
            basis.append(f"Official Meteorological Alert Level: RED issued by {a.source}.")
            basis.append(a.description)
            recs.extend([
                "Activate local district and community emergency response standard operating procedures (SOP).",
                "Evacuate vulnerable low-lying or landslide-prone settlements if directed by local authorities.",
                "Store 48 hours of potable drinking water, dry rations, and ensure emergency communications are charged."
            ])
            avoids.append("Do not enter flooded roads, inundated underpasses, or swollen streams under any circumstances.")
            valid_until_str = a.expires_at.strftime("%Y-%m-%d %H:%M UTC")
        elif orange_alerts:
            a = orange_alerts[0]
            verdict = "ELEVATED_RISK"
            icon = "⚠️"
            title = f"OFFICIAL ADVISORY: {a.headline}"
            basis.append(f"Official Alert Level: ORANGE issued by {a.source}.")
            basis.append(a.description)
            recs.extend([
                "Inspect municipal storm drains, clear debris, and stage emergency response pumps.",
                "Keep emergency medical first-aid kits and battery-operated lighting ready.",
                "Continuously monitor live weather bulletins and nowcast updates."
            ])
            avoids.append("Avoid non-essential transit during declared high-impact weather windows.")
            valid_until_str = a.expires_at.strftime("%Y-%m-%d %H:%M UTC")
        curr_temp = curr.temperature_c if curr.temperature_c is not None else 28.0
        curr_wind = curr.wind_speed_kmh if curr.wind_speed_kmh is not None else 0.0

        if curr_temp >= 41.0:
            verdict = "HEATWAVE_CAUTION"
            icon = "☀️"
            title = "Heat Stress / Heat Action Protocol"
            basis.append(
                f"Observed temperature reached {curr_temp:.1f}°C (Feels like {(curr.feels_like_c or curr_temp):.1f}°C)."
            )
            recs.extend([
                "Drink adequate water and oral rehydration salt (ORS) solutions frequently.",
                "Suspend strenuous outdoor manual labor between 12:00 PM and 03:30 PM."
            ])
            avoids.append("Avoid leaving children or elderly individuals in unventilated vehicles or closed spaces.")
        elif curr_wind >= 45.0:
            verdict = "ELEVATED_RISK"
            icon = "💨"
            title = "Strong Wind Hazard Advisory"
            basis.append(f"Strong winds are observed reaching {curr_wind:.1f} km/h.")
            recs.extend([
                "Secure tin roofs, loose construction scaffolding, and commercial signboards.",
                "Avoid standing or parking vehicles directly beneath old trees or overhead power cables."
            ])
            avoids.append("Avoid outdoor high-altitude work on rooftops or scaffolding.")
        else:
            verdict = "NORMAL"
            icon = "🛡️"
            title = "Disaster Preparedness Assessment"
            basis.append("All observed meteorological parameters are within seasonal tolerance levels.")
            recs.append("Maintain standard administrative standby readiness.")
            avoids.append("No active disaster avoidance restrictions.")

        return [
            SectorAdvisoryItem(
                sector="disaster",
                location=weather.location.name,
                title=title,
                recommendation=verdict,
                icon=icon,
                risk_level=level,
                risk_score=score,
                risk_factors=factors,
                weather_trigger=trigger,
                basis=basis,
                recommended_actions=recs,
                avoid_actions=avoids,
                valid_from=valid_from_str,
                valid_until=valid_until_str,
                sources=["Open-Meteo forecast"] + ([a.source for a in alerts] if alerts else []),
                confidence="Based on current forecast data",
                limitations=[
                    "System forecast indicators do not substitute for official statutory disaster decrees issued by District Disaster Management Authorities (DDMA) or State Disaster Management Authorities (SDMA)."
                ]
            )
        ]


class CitizenSectorModule(BaseSectorModule):
    """
    Daily life, commute safety, outdoor travel, umbrella recommendations.
    """

    def evaluate(
        self,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Dict[str, Any]
    ) -> List[SectorAdvisoryItem]:
        curr = weather.current
        daily = weather.daily
        tomorrow = daily[1] if len(daily) > 1 else (daily[0] if daily else None)

        now_utc = datetime.now(timezone.utc)
        valid_from_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
        valid_until_str = (now_utc + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M UTC")

        score, level, factors = risk_engine.calculate_risk(
            current=curr, daily=tomorrow, alerts=alerts, sector="citizen"
        )

        rain_prob = 0
        if curr.precipitation_probability_pct is not None:
            rain_prob = curr.precipitation_probability_pct
        elif daily and daily[0].precipitation_probability_max_pct is not None:
            rain_prob = daily[0].precipitation_probability_max_pct

        rain_mm = 0.0
        if curr.precipitation_mm is not None:
            rain_mm = curr.precipitation_mm
        elif daily and daily[0].precipitation_sum_mm is not None:
            rain_mm = daily[0].precipitation_sum_mm

        wind = curr.wind_speed_kmh or 0.0
        temp = curr.temperature_c or 25.0

        trigger = {
            "rain_probability_pct": rain_prob,
            "precipitation_mm": round(rain_mm, 1),
            "wind_speed_kmh": round(wind, 1),
            "temperature_c": round(temp, 1)
        }

        basis = []
        recs = []
        avoids = []

        if rain_prob >= 60 or rain_mm >= 2.0:
            verdict = "ALLOW_EXTRA_TRAVEL_TIME"
            icon = "🚗"
            title = "Commute & Road Safety Advisory"
            basis.append(f"Rain probability: {rain_prob}%. Possible slick asphalt and reduced braking friction.")
            recs.extend([
                "Carry an umbrella or waterproof rain gear.",
                "Maintain increased braking distance and use low-beam headlights in rain."
            ])
            avoids.append("Avoid traversing through unknown standing water or flooded road sections.")
        elif wind >= 35.0:
            verdict = "WIND_CAUTION"
            icon = "🛵"
            title = "Two-Wheeler Travel Advisory"
            basis.append(f"Strong crosswinds of {wind:.1f} km/h observed across open roadways.")
            recs.extend([
                "Two-wheeler riders should exercise caution on bridges, flyovers, and open highways.",
                "Reduce speed to maintain balance against sudden crosswind gusts."
            ])
            avoids.append("Avoid carrying oversized loads on two-wheelers during gusty periods.")
        else:
            verdict = "FAVORABLE_COMMUTE"
            icon = "🚲"
            title = "Commute & Outdoor Travel"
            basis.append("Dry roads and good horizontal atmospheric visibility.")
            recs.append("Conditions look favorable for commuting, cycling, and standard outdoor routines.")
            avoids.append("No adverse weather travel restrictions.")

        return [
            SectorAdvisoryItem(
                sector="citizen",
                location=weather.location.name,
                title=title,
                recommendation=verdict,
                icon=icon,
                risk_level=level,
                risk_score=score,
                risk_factors=factors,
                weather_trigger=trigger,
                basis=basis,
                recommended_actions=recs,
                avoid_actions=avoids,
                valid_from=valid_from_str,
                valid_until=valid_until_str,
                sources=["Open-Meteo forecast"],
                confidence="Based on current forecast data",
                limitations=[
                    "Localized street flooding depends on municipal drainage infrastructure, not solely regional precipitation."
                ]
            )
        ]


class MarineSectorModule(BaseSectorModule):
    """
    Coastal safety, fishermen advisory, sea-state and wind gust analysis.
    Explicitly declares wave/swell data limitations when wave data is unavailable.
    """

    def evaluate(
        self,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Dict[str, Any]
    ) -> List[SectorAdvisoryItem]:
        curr = weather.current
        daily = weather.daily
        tomorrow = daily[1] if len(daily) > 1 else (daily[0] if daily else None)

        now_utc = datetime.now(timezone.utc)
        valid_from_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
        valid_until_str = (now_utc + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M UTC")

        score, level, factors = risk_engine.calculate_risk(
            current=curr, daily=tomorrow, alerts=alerts, sector="marine"
        )

        wind = curr.wind_speed_kmh or 0.0
        gusts = curr.wind_gusts_kmh if curr.wind_gusts_kmh is not None else wind
        wmo = curr.weather_code or 0

        trigger = {
            "wind_speed_kmh": round(wind, 1),
            "wind_gusts_kmh": round(gusts, 1),
            "weather_code": wmo
        }

        basis = []
        recs = []
        avoids = []

        if wind >= 45.0 or gusts >= 55.0 or wmo in [95, 96, 99]:
            verdict = "DANGER_DO_NOT_VENTURE"
            icon = "🌊"
            title = "Fishermen Sea-Venture Warning"
            basis.append(f"Squally winds reaching {wind:.1f} km/h (gusts to {gusts:.1f} km/h) with convective weather.")
            recs.extend([
                "Fishermen are strictly advised not to venture into deep sea or coastal waters.",
                "Boats docked at coastal jetties must be securely double-moored."
            ])
            avoids.append("Do not operate small country crafts or mechanized fishing vessels.")
        elif wind >= 30.0:
            verdict = "CAUTION_ROUGH_SEA"
            icon = "⛵"
            title = "Coastal Marine Advisory"
            basis.append(f"Moderate to brisk coastal winds of {wind:.1f} km/h observed.")
            recs.extend([
                "Small boat operators should exercise caution and stay within close proximity to shorelines.",
                "Check marine VHF radio frequencies before departure."
            ])
            avoids.append("Avoid venturing into open offshore waters without functional life-saving equipment.")
        else:
            verdict = "MODERATE_SEA"
            icon = "⛵"
            title = "Coastal Marine Conditions"
            basis.append(f"Wind speed {wind:.1f} km/h is within safe sailing limits.")
            recs.append("Normal coastal sailing operations under standard maritime safety regulations.")
            avoids.append("Standard navigational precautions.")

        return [
            SectorAdvisoryItem(
                sector="marine",
                location=weather.location.name,
                title=title,
                recommendation=verdict,
                icon=icon,
                risk_level=level,
                risk_score=score,
                risk_factors=factors,
                weather_trigger=trigger,
                basis=basis,
                recommended_actions=recs,
                avoid_actions=avoids,
                valid_from=valid_from_str,
                valid_until=valid_until_str,
                sources=["Open-Meteo forecast"],
                confidence="Based on current forecast data",
                limitations=[
                    "Marine conditions cannot be fully assessed because wave/swell data is unavailable.",
                    "Do not rely solely on atmospheric forecasts for offshore navigation; always verify official INCOIS (Indian National Centre for Ocean Information Services) or IMD sea-state bulletins."
                ]
            )
        ]


class AviationSectorModule(BaseSectorModule):
    """
    Visibility, cross-wind, and convective thunderstorm hazards for general aviation and drones/UAV.
    Strictly provides general weather suitability guidance and never replaces official aviation weather services.
    """

    def evaluate(
        self,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Dict[str, Any]
    ) -> List[SectorAdvisoryItem]:
        curr = weather.current
        daily = weather.daily
        tomorrow = daily[1] if len(daily) > 1 else (daily[0] if daily else None)

        now_utc = datetime.now(timezone.utc)
        valid_from_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
        valid_until_str = (now_utc + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M UTC")

        score, level, factors = risk_engine.calculate_risk(
            current=curr, daily=tomorrow, alerts=alerts, sector="aviation"
        )

        vis = curr.visibility_km or 10.0
        wind = curr.wind_speed_kmh or 0.0
        gusts = curr.wind_gusts_kmh if curr.wind_gusts_kmh is not None else wind
        cloud = curr.cloud_cover_pct or 0
        wmo = curr.weather_code or 0

        trigger = {
            "visibility_km": round(vis, 1),
            "wind_speed_kmh": round(wind, 1),
            "wind_gusts_kmh": round(gusts, 1),
            "cloud_cover_pct": cloud,
            "weather_code": wmo
        }

        basis = []
        recs = []
        avoids = []

        if vis < 3.0 or gusts > 35.0 or wmo in [95, 96, 99]:
            verdict = "MARGINAL_OR_UNSUITABLE"
            icon = "✈️"
            title = "Aviation / Drone Weather Advisory"
            basis.append(f"Restricted atmospheric conditions: Visibility {vis:.1f} km, gusts to {gusts:.1f} km/h.")
            if wmo in [95, 96, 99]:
                basis.append("Active convective thunderstorm / lightning cells present.")
            recs.extend([
                "Ground all commercial drone/UAV flights due to turbulence and loss-of-sight risk.",
                "Verify certified airport METAR/TAF bulletins before any general aviation departure."
            ])
            avoids.append("Do not operate drones in low visibility or gusty conditions.")
        elif gusts > 25.0:
            verdict = "DRONE_WIND_CAUTION"
            icon = "🚁"
            title = "Drone / UAV Flight Advisory"
            basis.append(f"Moderate wind gusts reaching {gusts:.1f} km/h.")
            recs.extend([
                "Small multirotor drones (<2 kg) may experience motor saturation and reduced battery endurance.",
                "Fly in GPS-stabilized flight modes and avoid flying near tall structures."
            ])
            avoids.append("Avoid flying micro-drones above 50 meters AGL where wind shear increases.")
        else:
            verdict = "VFR_FAVORABLE"
            icon = "🛫"
            title = "Aviation / Flight Conditions"
            basis.append(f"Visibility is clear ({vis:.1f} km) with calm to moderate winds ({wind:.1f} km/h).")
            recs.append("Conditions appear suitable for visual drone flights and standard flight planning.")
            avoids.append("Always maintain visual line-of-sight (VLOS).")

        return [
            SectorAdvisoryItem(
                sector="aviation",
                location=weather.location.name,
                title=title,
                recommendation=verdict,
                icon=icon,
                risk_level=level,
                risk_score=score,
                risk_factors=factors,
                weather_trigger=trigger,
                basis=basis,
                recommended_actions=recs,
                avoid_actions=avoids,
                valid_from=valid_from_str,
                valid_until=valid_until_str,
                sources=["Open-Meteo forecast"],
                confidence="Based on current forecast data",
                limitations=[
                    "Insufficient data for an official aviation safety assessment.",
                    "Provides general weather suitability only. Certified pilots and drone operators must obtain official aerodrome METAR, TAF, and NOTAM information from statutory civil aviation authorities."
                ]
            )
        ]


class AdvisoryEngine:
    def __init__(self):
        self.modules = {
            "agriculture": AgricultureSectorModule(),
            "disaster": DisasterSectorModule(),
            "citizen": CitizenSectorModule(),
            "marine": MarineSectorModule(),
            "aviation": AviationSectorModule()
        }

    def generate_advisory(
        self,
        sector: str,
        weather: UnifiedWeatherResponse,
        alerts: List[WeatherAlert],
        context: Optional[Dict[str, Any]] = None
    ) -> SectorAdvisoryResponse:
        ctx = context or {}
        sec_key = sector.lower().strip()
        mod = self.modules.get(sec_key, self.modules["citizen"])
        items = mod.evaluate(weather, alerts, ctx)

        # Compute overall risk score and level across advisory items
        max_score = 0.0
        overall_risk = "LOW"
        for itm in items:
            if itm.risk_score > max_score:
                max_score = itm.risk_score
            if itm.risk_level == "CRITICAL":
                overall_risk = "CRITICAL"
            elif itm.risk_level == "HIGH" and overall_risk != "CRITICAL":
                overall_risk = "HIGH"
            elif itm.risk_level == "MEDIUM" and overall_risk not in ["CRITICAL", "HIGH"]:
                overall_risk = "MEDIUM"

        sources = ["Open-Meteo forecast"]
        if alerts:
            for a in alerts:
                if a.source not in sources:
                    sources.append(a.source)

        now_iso = datetime.now(timezone.utc).isoformat()

        official_alerts_data = [
            {
                "id": a.id,
                "headline": a.headline,
                "severity": a.severity.value,
                "source": a.source,
                "instruction": a.instruction,
                "expires_at": a.expires_at.isoformat()
            }
            for a in alerts
        ]

        return SectorAdvisoryResponse(
            location=weather.location.name,
            latitude=weather.location.latitude,
            longitude=weather.location.longitude,
            timezone=getattr(weather.location, "timezone", "UTC") or "UTC",
            sector=sec_key,
            overall_risk=overall_risk,
            overall_risk_score=max_score,
            advisories=items,
            recommendations=items,  # Backward compatibility alias
            weather_basis={
                "temperature_c": weather.current.temperature_c,
                "rain_mm": weather.current.precipitation_mm,
                "rain_prob_pct": weather.current.precipitation_probability_pct,
                "wind_kmh": weather.current.wind_speed_kmh,
                "humidity_pct": weather.current.relative_humidity_pct
            },
            sources=sources,
            generated_at=now_iso,
            official_alerts=official_alerts_data
        )


advisory_engine = AdvisoryEngine()
