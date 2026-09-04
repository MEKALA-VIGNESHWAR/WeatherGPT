import time
from typing import Dict, Any, List, Optional
from app.weather.fusion import fusion_service
from app.alerts.alert_service import warning_service
from app.weather.historical_service import historical_service
from app.gis.geo_service import geo_service
from app.advisory.advisory_engine import advisory_engine
from app.schemas.weather import UnifiedWeatherResponse
from app.schemas.alert import WeatherAlert, ActiveAlertsResponse
from app.schemas.advisory import SectorAdvisoryResponse
from app.core.logging import get_logger

logger = get_logger("ai.tools")


class WeatherToolRegistry:
    """
    Explicit tool definitions invoked by the Weather Intelligence Orchestrator.
    Tracks execution time and structured outputs.
    """

    @staticmethod
    async def get_current_weather(latitude: float, longitude: float, provider: Optional[str] = None) -> UnifiedWeatherResponse:
        t0 = time.time()
        res = await fusion_service.get_fused_weather(latitude, longitude, provider_name=provider, days=1)
        logger.info(f"tool:get_current_weather completed in {(time.time()-t0)*1000:.1f}ms")
        return res

    @staticmethod
    async def get_forecast(latitude: float, longitude: float, days: int = 7, provider: Optional[str] = None) -> UnifiedWeatherResponse:
        t0 = time.time()
        res = await fusion_service.get_fused_weather(latitude, longitude, provider_name=provider, days=days)
        logger.info(f"tool:get_forecast completed in {(time.time()-t0)*1000:.1f}ms")
        return res

    @staticmethod
    async def get_active_alerts(latitude: float, longitude: float, location_name: str = "Target Location") -> ActiveAlertsResponse:
        t0 = time.time()
        alerts = warning_service.get_alerts_for_location(latitude, longitude, location_name=location_name)
        logger.info(f"tool:get_active_alerts completed in {(time.time()-t0)*1000:.1f}ms")
        return alerts

    @staticmethod
    async def get_historical_weather(latitude: float, longitude: float) -> Dict[str, Any]:
        t0 = time.time()
        res = await historical_service.get_rainfall_trend_7days(latitude, longitude)
        logger.info(f"tool:get_historical_weather completed in {(time.time()-t0)*1000:.1f}ms")
        return res

    @staticmethod
    async def get_climate_trend(latitude: float, longitude: float, period: str = "7_days") -> Dict[str, Any]:
        t0 = time.time()
        res = await historical_service.get_climate_trend(latitude, longitude, period=period)
        logger.info(f"tool:get_climate_trend completed in {(time.time()-t0)*1000:.1f}ms")
        return res

    @staticmethod
    async def get_location(place_name: str) -> List[Dict[str, Any]]:
        t0 = time.time()
        places = await geo_service.search_places(place_name)
        logger.info(f"tool:get_location completed in {(time.time()-t0)*1000:.1f}ms")
        return [p.model_dump() for p in places]

    @staticmethod
    async def get_agriculture_advisory(
        latitude: float, longitude: float, crop: Optional[str] = None
    ) -> SectorAdvisoryResponse:
        t0 = time.time()
        weather = await fusion_service.get_fused_weather(latitude, longitude, days=7)
        alerts = warning_service.get_alerts_for_location(latitude, longitude).alerts
        res = advisory_engine.generate_advisory("agriculture", weather, alerts, {"crop": crop or "paddy"})
        logger.info(f"tool:get_agriculture_advisory completed in {(time.time()-t0)*1000:.1f}ms")
        return res


weather_tools = WeatherToolRegistry()
