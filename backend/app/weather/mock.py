from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from app.weather.base import BaseWeatherProvider
from app.schemas.weather import (
    CurrentWeather, HourlyForecastPoint, DailyForecastPoint,
    UnifiedWeatherResponse, LocationInfo, TrustMetadata, ConfidenceLevel, ModelAgreement
)
from app.schemas.alert import WeatherAlert, AlertSeverity, AlertType


class MockProvider(BaseWeatherProvider):
    """
    Mock weather provider strictly for deterministic development, testing, and offline demonstrations.
    All outputs are explicitly flagged with `is_demo_data = True`.
    """
    @property
    def provider_name(self) -> str:
        return "WeatherGPT Demo Provider (SYNTHETIC BENCHMARK)"

    @property
    def is_demo(self) -> bool:
        return True

    async def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        forecast = await self.get_forecast(latitude, longitude, days=1)
        return forecast.current

    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> UnifiedWeatherResponse:
        utc_now = datetime.now(timezone.utc)
        local_now = datetime.now().astimezone()
        
        # Coordinate-based pseudo-deterministic variability
        coord_hash = int(abs(latitude * 100) + abs(longitude * 100)) % 100
        temp_base = 23.0 + (coord_hash % 14)  # 23.0 to 36.0 C
        feels_diff = 2.0 if temp_base > 28 else -1.0
        humid_base = 45 + (coord_hash % 45)   # 45% to 89%
        prob_base = 15 + ((coord_hash * 7) % 70) # 15% to 84%
        is_rainy = prob_base >= 55
        
        current = CurrentWeather(
            temperature_c=round(temp_base, 1),
            feels_like_c=round(temp_base + feels_diff, 1),
            relative_humidity_pct=humid_base,
            wind_speed_kmh=round(10.0 + (coord_hash % 16), 1),
            wind_direction_deg=(coord_hash * 25) % 360,
            wind_gusts_kmh=round(16.0 + (coord_hash % 15), 1),
            precipitation_mm=round(3.5 + (prob_base / 20.0), 1) if is_rainy else 0.0,
            precipitation_probability_pct=prob_base,
            surface_pressure_hpa=round(1008.0 + (coord_hash % 12) - 6, 1),
            visibility_km=7.0 if is_rainy else 10.0,
            uv_index=round(min(11.0, max(1.0, 3.5 + (coord_hash % 6))), 1),
            weather_code=61 if is_rainy else (2 if prob_base > 30 else 0),
            weather_condition="Light rain" if is_rainy else ("Partly cloudy" if prob_base > 30 else "Clear sky"),
            weather_icon="🌦️" if is_rainy else ("⛅" if prob_base > 30 else "☀️"),
            sunrise="06:00",
            sunset="18:30"
        )

        hourly: List[HourlyForecastPoint] = []
        for h in range(72):
            t_dt = local_now + timedelta(hours=h)
            h_cycle = 4.0 * (1.0 - abs(t_dt.hour - 14) / 10.0)
            h_prob = min(95, max(10, prob_base + int(15 * ((h % 5) - 2))))
            h_rain = h_prob >= 55
            hourly.append(
                HourlyForecastPoint(
                    time=t_dt.strftime("%Y-%m-%dT%H:00"),
                    temperature_c=round(temp_base + h_cycle + ((h % 3) - 1) * 0.4, 1),
                    relative_humidity_pct=min(98, max(30, humid_base - int(h_cycle * 2))),
                    precipitation_probability_pct=h_prob,
                    precipitation_mm=round(2.0 + (h_prob / 25.0), 1) if h_rain else 0.0,
                    wind_speed_kmh=round(10.0 + ((h + coord_hash) % 12), 1),
                    weather_code=61 if h_rain else (2 if h_prob > 30 else 0),
                    weather_condition="Light rain" if h_rain else ("Partly cloudy" if h_prob > 30 else "Clear sky"),
                    weather_icon="🌦️" if h_rain else ("⛅" if h_prob > 30 else "☀️")
                )
            )

        daily: List[DailyForecastPoint] = []
        for d in range(days):
            d_dt = local_now + timedelta(days=d)
            d_prob = min(95, max(15, prob_base + ((d * 13) % 40) - 20))
            d_rain = d_prob >= 60
            daily.append(
                DailyForecastPoint(
                    date=d_dt.strftime("%Y-%m-%d"),
                    temperature_max_c=round(temp_base + 3.5, 1),
                    temperature_min_c=round(temp_base - 5.0, 1),
                    precipitation_probability_max_pct=d_prob,
                    precipitation_sum_mm=round(12.0 + (d_prob / 5.0), 1) if d_rain else 1.0,
                    wind_speed_max_kmh=round(15.0 + (coord_hash % 10), 1),
                    weather_code=63 if d_rain else (1 if d_prob < 35 else 2),
                    weather_condition="Moderate rain" if d_rain else ("Mainly clear" if d_prob < 35 else "Partly cloudy"),
                    weather_icon="🌧️" if d_rain else ("🌤️" if d_prob < 35 else "⛅"),
                    sunrise="06:00",
                    sunset="18:30",
                    uv_index_max=round(min(11.0, max(2.0, 5.0 + (coord_hash % 5))), 1)
                )
            )

        trust = TrustMetadata(
            source=self.provider_name,
            observed_at=utc_now,
            retrieved_at=utc_now,
            data_age_minutes=0.1,
            source_authority="synthetic_demo_model",
            confidence=ConfidenceLevel.HIGH,
            model_agreement=ModelAgreement.HIGH,
            is_demo_data=True
        )

        return UnifiedWeatherResponse(
            location=LocationInfo(
                name="Target Location",
                latitude=latitude,
                longitude=longitude,
                state="State",
                country="India",
                elevation_m=500.0
            ),
            current=current,
            hourly=hourly,
            daily=daily,
            trust=trust,
            raw_sources_fused=["Simulated AWS Station", "Synthetic NWP Grid"]
        )

    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        return {
            "time": ["2026-08-28", "2026-08-29", "2026-08-30", "2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03"],
            "temperature_2m_max": [31.2, 32.0, 30.5, 29.8, 31.0, 32.4, 30.8],
            "temperature_2m_min": [23.1, 23.5, 22.8, 22.4, 23.0, 23.8, 22.9],
            "precipitation_sum": [4.2, 12.8, 22.0, 0.5, 0.0, 6.4, 15.2],
            "wind_speed_10m_max": [16.2, 18.0, 22.4, 14.0, 12.5, 15.0, 19.2]
        }

    async def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        now = datetime.now(timezone.utc)
        return [
            WeatherAlert(
                id="DEMO-ALERT-2026-01",
                headline="Thunderstorm and Moderate Lightning Alert",
                description="Moderate thunderstorm accompanied by lightning and gusty winds (30-40 km/h) likely to occur.",
                instruction="Farmers are advised to postpone pesticide spraying and secure harvested crops in shelters.",
                severity=AlertSeverity.YELLOW,
                alert_type=AlertType.THUNDERSTORM,
                source="IMD / WeatherGPT Simulated Alert",
                area_desc="Hyderabad & Rangareddy Districts",
                effective_from=now,
                expires_at=now + timedelta(hours=24),
                latitude=latitude,
                longitude=longitude,
                radius_km=45.0,
                color_code="#FFCC00"
            )
        ]
