import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "WeatherGPT"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Debug
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = False  # If True, returns marked demo data
    
    # Security
    JWT_SECRET: str = "dev_secret_super_secure_key_for_weathergpt_sih_2026_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./weathergpt.db"
    SYNC_DATABASE_URL: str = "sqlite:///./weathergpt.db"
    POSTGIS_ENABLED: bool = False
    
    # Redis Cache (Optional - in-memory fallback enabled)
    REDIS_URL: Optional[str] = None
    WEATHER_CACHE_TTL_SECONDS: int = 600  # 10 minutes
    FORECAST_CACHE_TTL_SECONDS: int = 1800 # 30 minutes
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: str = "openai"  # "openai" or "mock" / "rule_based"
    
    # Weather APIs
    DEFAULT_WEATHER_PROVIDER: str = "open_meteo"  # open_meteo | imd | gfs | wrf | mock
    IMD_API_BASE_URL: Optional[str] = "https://mausam.imd.gov.in/api"
    IMD_API_KEY: Optional[str] = None
    GFS_BASE_URL: Optional[str] = "https://nomads.ncep.noaa.gov"
    WRF_BASE_URL: Optional[str] = None
    
    # Voice STT / TTS
    STT_PROVIDER: str = "browser"  # browser | whisper
    TTS_PROVIDER: str = "browser"  # browser | gtts | open_tts
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
