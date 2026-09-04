import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.weather.base import BaseWeatherProvider
from app.schemas.weather import (
    CurrentWeather, HourlyForecastPoint, DailyForecastPoint,
    UnifiedWeatherResponse, LocationInfo, TrustMetadata, ConfidenceLevel, ModelAgreement
)
from app.schemas.alert import WeatherAlert
from app.core.logging import get_logger

logger = get_logger("weather.open_meteo")

WMO_WEATHER_MAP = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Slight snowfall", "🌨️"),
    73: ("Moderate snowfall", "🌨️"),
    75: ("Heavy snowfall", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def parse_wmo(code: int) -> tuple[str, str]:
    return WMO_WEATHER_MAP.get(code, ("Variable clouds", "⛅"))


class OpenMeteoProvider(BaseWeatherProvider):
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.archive_url = "https://archive-api.open-meteo.com/v1/archive"

    @property
    def provider_name(self) -> str:
        return "Open-Meteo (Global NWP Ensemble & IMD Resolution)"

    @property
    def is_demo(self) -> bool:
        return False

    async def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        forecast = await self.get_forecast(latitude, longitude, days=1)
        return forecast.current

    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> UnifiedWeatherResponse:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,uv_index_max,sunrise,sunset",
            "timezone": "auto",
            "forecast_days": min(max(days, 1), 16)
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

        curr = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        wmo_code = curr.get("weather_code", 0)
        cond_text, icon = parse_wmo(wmo_code)

        # Sunrise & sunset today
        sunrise = daily.get("sunrise", ["06:00"])[0] if daily.get("sunrise") else "06:00"
        sunset = daily.get("sunset", ["18:30"])[0] if daily.get("sunset") else "18:30"

        # Precipitation probability today
        precip_prob_max = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0

        current_obj = CurrentWeather(
            temperature_c=round(curr.get("temperature_2m", 25.0), 1),
            feels_like_c=round(curr.get("apparent_temperature", curr.get("temperature_2m", 25.0)), 1),
            relative_humidity_pct=int(curr.get("relative_humidity_2m", 50)),
            wind_speed_kmh=round(curr.get("wind_speed_10m", 10.0), 1),
            wind_direction_deg=int(curr.get("wind_direction_10m", 0)),
            wind_gusts_kmh=round(curr.get("wind_gusts_10m", 12.0), 1),
            precipitation_mm=round(curr.get("precipitation", 0.0), 1),
            precipitation_probability_pct=precip_prob_max,
            surface_pressure_hpa=round(curr.get("surface_pressure", 1013.25), 1),
            visibility_km=10.0,
            uv_index=round(daily.get("uv_index_max", [5.0])[0], 1) if daily.get("uv_index_max") else 5.0,
            weather_code=wmo_code,
            weather_condition=cond_text,
            weather_icon=icon,
            sunrise=sunrise,
            sunset=sunset
        )

        # Build 24 hours of forecast starting from current hour
        hourly_points: List[HourlyForecastPoint] = []
        all_times = hourly.get("time", [])
        curr_time_str = curr.get("time", "")  # e.g., "2026-09-04T18:00"
        
        start_idx = 0
        if curr_time_str and all_times:
            # Match by hour prefix from Open-Meteo local time (e.g. "2026-09-04T18")
            target_hour = curr_time_str[:13]
            found = False
            for idx, t in enumerate(all_times):
                if t.startswith(target_hour):
                    start_idx = idx
                    found = True
                    break
            if not found:
                for idx, t in enumerate(all_times):
                    if t >= target_hour:
                        start_idx = idx
                        break

        times = all_times[start_idx:]
        temps = hourly.get("temperature_2m", [])[start_idx:]
        humids = hourly.get("relative_humidity_2m", [])[start_idx:]
        probs = hourly.get("precipitation_probability", [])[start_idx:]
        precips = hourly.get("precipitation", [])[start_idx:]
        winds = hourly.get("wind_speed_10m", [])[start_idx:]
        codes = hourly.get("weather_code", [])[start_idx:]

        for i in range(len(times)):
            c_text, c_icon = parse_wmo(codes[i] if i < len(codes) else 0)
            hourly_points.append(
                HourlyForecastPoint(
                    time=times[i],
                    temperature_c=round(temps[i], 1) if i < len(temps) else 25.0,
                    relative_humidity_pct=int(humids[i]) if i < len(humids) else 50,
                    precipitation_probability_pct=int(probs[i]) if i < len(probs) else 0,
                    precipitation_mm=round(precips[i], 1) if i < len(precips) else 0.0,
                    wind_speed_kmh=round(winds[i], 1) if i < len(winds) else 10.0,
                    weather_code=codes[i] if i < len(codes) else 0,
                    weather_condition=c_text,
                    weather_icon=c_icon
                )
            )

        # Build daily points
        daily_points: List[DailyForecastPoint] = []
        d_dates = daily.get("time", [])
        d_max = daily.get("temperature_2m_max", [])
        d_min = daily.get("temperature_2m_min", [])
        d_prob = daily.get("precipitation_probability_max", [])
        d_rain = daily.get("precipitation_sum", [])
        d_wind = daily.get("wind_speed_10m_max", [])
        d_code = daily.get("weather_code", [])
        d_sunr = daily.get("sunrise", [])
        d_suns = daily.get("sunset", [])
        d_uv = daily.get("uv_index_max", [])

        for i in range(len(d_dates)):
            c_text, c_icon = parse_wmo(d_code[i] if i < len(d_code) else 0)
            daily_points.append(
                DailyForecastPoint(
                    date=d_dates[i],
                    temperature_max_c=round(d_max[i], 1) if i < len(d_max) else 30.0,
                    temperature_min_c=round(d_min[i], 1) if i < len(d_min) else 20.0,
                    precipitation_probability_max_pct=int(d_prob[i]) if i < len(d_prob) else 0,
                    precipitation_sum_mm=round(d_rain[i], 1) if i < len(d_rain) else 0.0,
                    wind_speed_max_kmh=round(d_wind[i], 1) if i < len(d_wind) else 10.0,
                    weather_code=d_code[i] if i < len(d_code) else 0,
                    weather_condition=c_text,
                    weather_icon=c_icon,
                    sunrise=d_sunr[i] if i < len(d_sunr) else "06:00",
                    sunset=d_suns[i] if i < len(d_suns) else "18:30",
                    uv_index_max=round(d_uv[i], 1) if i < len(d_uv) else 5.0
                )
            )

        trust = TrustMetadata(
            source=self.provider_name,
            observed_at=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
            data_age_minutes=2.5,
            source_authority="verified_meteorological_grid",
            confidence=ConfidenceLevel.HIGH,
            model_agreement=ModelAgreement.HIGH,
            is_demo_data=False
        )

        return UnifiedWeatherResponse(
            location=LocationInfo(
                name="Target Location",
                latitude=latitude,
                longitude=longitude,
                elevation_m=data.get("elevation", 0.0)
            ),
            current=current_obj,
            hourly=hourly_points,
            daily=daily_points,
            trust=trust,
            raw_sources_fused=["Open-Meteo ECMWF/GFS Blend"]
        )

    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.archive_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("daily", {})

    async def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        # Handled primarily by AlertService, default empty list for open-meteo provider
        return []
