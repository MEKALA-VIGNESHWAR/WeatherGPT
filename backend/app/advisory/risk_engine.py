from typing import List, Tuple, Optional, Dict, Any
from app.schemas.weather import CurrentWeather, DailyForecastPoint
from app.schemas.alert import WeatherAlert, AlertSeverity


class RiskEngine:
    """
    Explainable, deterministic meteorological risk calculation engine.
    Derives risk score (0-100), risk level (LOW, MEDIUM, HIGH, CRITICAL),
    and the explicit contributing factors from actual weather observations & forecasts.
    """

    @staticmethod
    def calculate_risk(
        current: CurrentWeather,
        daily: Optional[DailyForecastPoint] = None,
        alerts: Optional[List[WeatherAlert]] = None,
        sector: str = "general",
        crop: Optional[str] = None
    ) -> Tuple[float, str, List[str]]:
        score = 0.0
        factors: List[str] = []

        # 1. Rain Probability & Expected Accumulation
        rain_prob = 0
        if daily and daily.precipitation_probability_max_pct is not None:
            rain_prob = daily.precipitation_probability_max_pct
        elif current.precipitation_probability_pct is not None:
            rain_prob = current.precipitation_probability_pct

        rain_mm = 0.0
        if daily and daily.precipitation_sum_mm is not None:
            rain_mm = daily.precipitation_sum_mm
        elif current.precipitation_mm is not None:
            rain_mm = current.precipitation_mm

        if rain_prob >= 75:
            score += 35.0
            factors.append(f"Very high precipitation probability ({rain_prob}%)")
        elif rain_prob >= 50:
            score += 20.0
            factors.append(f"Elevated precipitation probability ({rain_prob}%)")
        elif rain_prob >= 25:
            score += 10.0
            factors.append(f"Moderate precipitation probability ({rain_prob}%)")

        if rain_mm >= 30.0:
            score += 30.0
            factors.append(f"Heavy rainfall accumulation forecast ({rain_mm:.1f} mm)")
        elif rain_mm >= 15.0:
            score += 20.0
            factors.append(f"Moderate to heavy rainfall forecast ({rain_mm:.1f} mm)")
        elif rain_mm >= 5.0:
            score += 10.0
            factors.append(f"Noticeable rainfall accumulation ({rain_mm:.1f} mm)")

        # 2. Wind & Gusts
        wind_speed = 0.0
        if daily and daily.wind_speed_max_kmh is not None:
            wind_speed = daily.wind_speed_max_kmh
        elif current.wind_speed_kmh is not None:
            wind_speed = current.wind_speed_kmh

        wind_gusts = wind_speed
        if daily and daily.wind_gusts_max_kmh is not None:
            wind_gusts = daily.wind_gusts_max_kmh
        elif current.wind_gusts_kmh is not None:
            wind_gusts = current.wind_gusts_kmh

        if wind_speed >= 50.0 or wind_gusts >= 65.0:
            score += 35.0
            factors.append(f"Squally wind speeds ({wind_speed:.1f} km/h, gusts to {wind_gusts:.1f} km/h)")
        elif wind_speed >= 30.0 or wind_gusts >= 40.0:
            score += 20.0
            factors.append(f"Brisk or gusty winds ({wind_speed:.1f} km/h, gusts to {wind_gusts:.1f} km/h)")
        elif wind_speed >= 18.0:
            if sector.lower() == "agriculture":
                score += 10.0
                factors.append(f"Wind speed ({wind_speed:.1f} km/h) creates spray drift hazard")

        # 3. Severe Weather Codes (WMO)
        wmo = 0
        if daily and daily.weather_code is not None:
            wmo = daily.weather_code
        elif current.weather_code is not None:
            wmo = current.weather_code

        # 95: Thunderstorm, 96/99: Thunderstorm with hail, 80-82: Showers, 71-77: Snow
        if wmo in [95, 96, 99]:
            score += 30.0
            factors.append("Active convective thunderstorm / lightning risk")
        elif wmo in [81, 82]:
            score += 15.0
            factors.append("Violent or torrential rain showers")

        # 4. Temperature Extremes (Heatwave / Frost)
        temp_max = 28.0
        if daily and daily.temperature_max_c is not None:
            temp_max = daily.temperature_max_c
        elif current.temperature_c is not None:
            temp_max = current.temperature_c

        temp_min = 20.0
        if daily and daily.temperature_min_c is not None:
            temp_min = daily.temperature_min_c
        elif current.temperature_c is not None:
            temp_min = current.temperature_c

        if temp_max >= 43.0:
            score += 30.0
            factors.append(f"Severe heatwave conditions ({temp_max:.1f}°C)")
        elif temp_max >= 40.0:
            score += 18.0
            factors.append(f"Elevated heat stress ({temp_max:.1f}°C)")
        elif temp_min <= 2.0:
            score += 25.0
            factors.append(f"Near-freezing temperatures / frost hazard ({temp_min:.1f}°C)")

        # 5. Verified Official Government / Meteorological Alerts
        if alerts:
            for alert in alerts:
                if alert.severity == AlertSeverity.RED:
                    score += 45.0
                    factors.append(f"Official RED Alert: {alert.headline} ({alert.source})")
                elif alert.severity == AlertSeverity.ORANGE:
                    score += 30.0
                    factors.append(f"Official ORANGE Alert: {alert.headline} ({alert.source})")
                elif alert.severity == AlertSeverity.YELLOW:
                    score += 15.0
                    factors.append(f"Official YELLOW Advisory: {alert.headline} ({alert.source})")

        # Cap score between 0 and 100
        final_score = min(100.0, max(0.0, round(score, 1)))

        # Derive categorical level
        if final_score >= 80.0:
            level = "CRITICAL"
        elif final_score >= 50.0:
            level = "HIGH"
        elif final_score >= 25.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not factors:
            factors.append("All observed meteorological parameters are within normal baseline thresholds")

        return final_score, level, factors


risk_engine = RiskEngine()
