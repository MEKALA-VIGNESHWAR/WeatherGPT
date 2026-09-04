from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.weather.base import BaseWeatherProvider
from app.weather.open_meteo import OpenMeteoProvider
from app.weather.imd import IMDProvider
from app.weather.nwp import GFSProvider, WRFProvider
from app.weather.mock import MockProvider
from app.schemas.weather import (
    UnifiedWeatherResponse, CurrentWeather, TrustMetadata,
    ConfidenceLevel, ModelAgreement, LocationInfo
)
from app.core.config import settings
from app.core.cache import cache_service
from app.core.logging import get_logger

logger = get_logger("weather.fusion")


class DataFusionService:
    def __init__(self):
        self.providers: Dict[str, BaseWeatherProvider] = {
            "open_meteo": OpenMeteoProvider(),
            "imd": IMDProvider(),
            "gfs": GFSProvider(),
            "wrf": WRFProvider(),
            "mock": MockProvider()
        }

    def get_provider(self, name: Optional[str] = None) -> BaseWeatherProvider:
        if settings.DEMO_MODE:
            return self.providers["mock"]
        prov_name = (name or settings.DEFAULT_WEATHER_PROVIDER).lower()
        return self.providers.get(prov_name, self.providers["open_meteo"])

    async def get_fused_weather(
        self, latitude: float, longitude: float, provider_name: Optional[str] = None, days: int = 7
    ) -> UnifiedWeatherResponse:
        """
        Retrieves weather data, validates coordinates, checks cache,
        computes freshness, and attaches Trust Metadata.
        """
        # Coordinate sanity check
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError(f"Coordinates out of bounds: lat={latitude}, lon={longitude}")

        cache_key = f"weather:{round(latitude, 3)}:{round(longitude, 3)}:{provider_name}:{days}"
        cached = cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for weather at ({latitude}, {longitude})")
            return UnifiedWeatherResponse.model_validate(cached)

        provider = self.get_provider(provider_name)
        logger.info(f"Retrieving weather from provider: {provider.provider_name}")

        try:
            weather_resp = await provider.get_forecast(latitude, longitude, days=days)
        except Exception as e:
            logger.error(f"Provider {provider.provider_name} failed: {e}. Falling back to Open-Meteo.")
            weather_resp = await self.providers["open_meteo"].get_forecast(latitude, longitude, days=days)
            weather_resp.trust.confidence = ConfidenceLevel.MEDIUM
            weather_resp.trust.source += " (Failover Active)"

        # Calculate data freshness
        now = datetime.now(timezone.utc)
        data_age = (now - weather_resp.trust.observed_at).total_seconds() / 60.0
        weather_resp.trust.data_age_minutes = max(0.1, round(data_age, 1))

        if weather_resp.trust.data_age_minutes > 120:
            weather_resp.trust.confidence = ConfidenceLevel.LOW
        elif weather_resp.trust.data_age_minutes > 45:
            weather_resp.trust.confidence = ConfidenceLevel.MEDIUM

        # Cache response
        cache_service.set(cache_key, weather_resp.model_dump(), ttl_seconds=settings.WEATHER_CACHE_TTL_SECONDS)

        return weather_resp


fusion_service = DataFusionService()
