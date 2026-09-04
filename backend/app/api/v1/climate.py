from fastapi import APIRouter, Query, HTTPException
from app.weather.historical_service import historical_service

router = APIRouter(prefix="/climate", tags=["Climate & Long-term Analytics"])


@router.get("/trends")
async def get_climate_trends(
    latitude: float = Query(17.3850, ge=-90, le=90),
    longitude: float = Query(78.4867, ge=-180, le=180),
    period: str = Query("7_days")
):
    try:
        return await historical_service.get_climate_trend(latitude, longitude, period=period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
