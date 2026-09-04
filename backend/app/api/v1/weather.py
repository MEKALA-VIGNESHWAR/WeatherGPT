from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from app.weather.fusion import fusion_service
from app.weather.historical_service import historical_service
from app.gis.geo_service import geo_service
from app.schemas.weather import UnifiedWeatherResponse, CurrentWeather

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/current", response_model=CurrentWeather)
async def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    provider: Optional[str] = Query(None)
):
    try:
        fused = await fusion_service.get_fused_weather(latitude, longitude, provider_name=provider, days=1)
        return fused.current
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast", response_model=UnifiedWeatherResponse)
async def get_weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=16),
    provider: Optional[str] = Query(None),
    location_name: Optional[str] = Query(None)
):
    try:
        fused = await fusion_service.get_fused_weather(latitude, longitude, provider_name=provider, days=days)
        
        # If client explicitly specified a location name, respect it
        if location_name and location_name.strip():
            fused.location.name = location_name.strip()
        elif fused.location.name in ["Target Location", "Demo Station (Hyderabad)", "Unknown Location"] or "Demo Station" in (fused.location.name or ""):
            geo_res = await geo_service.reverse_geocode(latitude, longitude)
            if geo_res and geo_res.name:
                fused.location.name = geo_res.name
                if geo_res.state:
                    fused.location.state = geo_res.state
                if geo_res.country:
                    fused.location.country = geo_res.country
        return fused
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    period: str = Query("7_days")
):
    try:
        return await historical_service.get_climate_trend(latitude, longitude, period=period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
