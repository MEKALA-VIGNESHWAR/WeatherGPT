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
        now = datetime.now(timezone.utc)
        
        # Deterministic sample conditions: monsoon / light shower scenario
        current = CurrentWeather(
            temperature_c=28.4,
            feels_like_c=31.2,
            relative_humidity_pct=78,
            wind_speed_kmh=14.5,
            wind_direction_deg=220,
            wind_gusts_kmh=22.0,
            precipitation_mm=2.5,
            precipitation_probability_pct=65,
            surface_pressure_hpa=1008.4,
            visibility_km=8.0,
            uv_index=4.2,
            weather_code=61,
            weather_condition="Light rain",
            weather_icon="🌦️",
            sunrise="05:58",
            sunset="18:32"
        )

        hourly: List[HourlyForecastPoint] = []
        for h in range(24):
            t_dt = now + timedelta(hours=h)
            prob = 75 if 8 <= t_dt.hour <= 16 else 30
            hourly.append(
                HourlyForecastPoint(
                    time=t_dt.strftime("%Y-%m-%dT%H:00"),
                    temperature_c=round(26.0 + 4.0 * (1.0 - abs(t_dt.hour - 14) / 10), 1),
                    relative_humidity_pct=min(95, max(50, 85 - (t_dt.hour % 8) * 3)),
                    precipitation_probability_pct=prob,
                    precipitation_mm=3.2 if prob > 50 else 0.0,
                    wind_speed_kmh=12.0 + (h % 5),
                    weather_code=61 if prob > 50 else 2,
                    weather_condition="Light rain" if prob > 50 else "Partly cloudy",
                    weather_icon="🌦️" if prob > 50 else "⛅"
                )
            )

        daily: List[DailyForecastPoint] = []
        for d in range(days):
            d_dt = now + timedelta(days=d)
            prob = 80 if d == 1 else (40 if d % 2 == 0 else 60)
            daily.append(
                DailyForecastPoint(
                    date=d_dt.strftime("%Y-%m-%d"),
                    temperature_max_c=32.5,
                    temperature_min_c=23.0,
                    precipitation_probability_max_pct=prob,
                    precipitation_sum_mm=18.4 if prob > 70 else 2.0,
                    wind_speed_max_kmh=18.0,
                    weather_code=63 if prob > 70 else 1,
                    weather_condition="Moderate rain" if prob > 70 else "Mainly clear",
                    weather_icon="🌧️" if prob > 70 else "🌤️",
                    sunrise="05:58",
                    sunset="18:32",
                    uv_index_max=6.5
                )
            )

        trust = TrustMetadata(
            source=self.provider_name,
            observed_at=now,
            retrieved_at=now,
            data_age_minutes=0.1,
            source_authority="synthetic_demo_model",
            confidence=ConfidenceLevel.HIGH,
            model_agreement=ModelAgreement.HIGH,
            is_demo_data=True
        )

        return UnifiedWeatherResponse(
            location=LocationInfo(
                name="Demo Station (Hyderabad)",
                latitude=latitude,
                longitude=longitude,
                state="Telangana",
                country="India",
                elevation_m=542.0
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
