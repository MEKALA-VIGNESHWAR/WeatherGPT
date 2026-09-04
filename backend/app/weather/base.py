from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.schemas.weather import CurrentWeather, HourlyForecastPoint, DailyForecastPoint, UnifiedWeatherResponse
from app.schemas.alert import WeatherAlert


class BaseWeatherProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the weather provider (e.g., 'Open-Meteo', 'IMD', 'GFS', 'WRF', 'Mock')"""
        pass

    @property
    @abstractmethod
    def is_demo(self) -> bool:
        """Whether this provider produces mock/simulated demo data"""
        pass

    @abstractmethod
    async def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        """Fetch current normalized weather observation"""
        pass

    @abstractmethod
    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> UnifiedWeatherResponse:
        """Fetch normalized multi-day forecast with hourly details"""
        pass

    @abstractmethod
    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Fetch historical weather series between start_date and end_date (YYYY-MM-DD)"""
        pass

    @abstractmethod
    async def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        """Fetch active meteorological warnings for coordinates"""
        pass
