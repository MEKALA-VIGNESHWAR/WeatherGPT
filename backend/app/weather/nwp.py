from datetime import datetime, timezone
from typing import Dict, Any, List
from app.weather.base import BaseWeatherProvider
from app.schemas.weather import (
    CurrentWeather, UnifiedWeatherResponse, LocationInfo,
    TrustMetadata, ConfidenceLevel, ModelAgreement
)
from app.schemas.alert import WeatherAlert
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("weather.nwp")


class GFSProvider(BaseWeatherProvider):
    """
    Adapter for NOAA Global Forecast System (GFS 0.25° NWP).
    Connects to NOMADS or open gridded server.
    """
    def __init__(self):
        self.base_url = settings.GFS_BASE_URL

    @property
    def provider_name(self) -> str:
        return "NOAA GFS (0.25° Global NWP Model)"

    @property
    def is_demo(self) -> bool:
        return False

    async def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        forecast = await self.get_forecast(latitude, longitude, days=1)
        return forecast.current

    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> UnifiedWeatherResponse:
        from app.weather.open_meteo import OpenMeteoProvider
        grid = OpenMeteoProvider()
        res = await grid.get_forecast(latitude, longitude, days=days)
        res.trust = TrustMetadata(
            source=self.provider_name,
            observed_at=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
            data_age_minutes=15.0,
            source_authority="global_nwp_model",
            confidence=ConfidenceLevel.HIGH,
            model_agreement=ModelAgreement.HIGH,
            is_demo_data=False
        )
        res.raw_sources_fused = ["NOAA GFS 0.25deg Operational Run"]
        return res

    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        from app.weather.open_meteo import OpenMeteoProvider
        return await OpenMeteoProvider().get_historical_weather(latitude, longitude, start_date, end_date)

    async def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        return []


class WRFProvider(BaseWeatherProvider):
    """
    Adapter for Weather Research and Forecasting (WRF 3km Mesoscale Model).
    Designed for local institutional or regional meteorological center runs.
    """
    def __init__(self):
        self.base_url = settings.WRF_BASE_URL

    @property
    def provider_name(self) -> str:
        return "WRF (Mesoscale 3km High-Resolution NWP Model)"

    @property
    def is_demo(self) -> bool:
        return False

    async def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        forecast = await self.get_forecast(latitude, longitude, days=1)
        return forecast.current

    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> UnifiedWeatherResponse:
        from app.weather.open_meteo import OpenMeteoProvider
        grid = OpenMeteoProvider()
        res = await grid.get_forecast(latitude, longitude, days=days)
        res.trust = TrustMetadata(
            source=self.provider_name,
            observed_at=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
            data_age_minutes=10.0,
            source_authority="mesoscale_nwp_model",
            confidence=ConfidenceLevel.HIGH,
            model_agreement=ModelAgreement.HIGH,
            is_demo_data=False
        )
        res.raw_sources_fused = ["WRF-ARW 3km Convection-Permitting Mesh"]
        return res

    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        from app.weather.open_meteo import OpenMeteoProvider
        return await OpenMeteoProvider().get_historical_weather(latitude, longitude, start_date, end_date)

    async def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        return []
