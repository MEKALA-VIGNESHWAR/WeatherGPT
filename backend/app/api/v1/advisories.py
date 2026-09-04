from fastapi import APIRouter, Query, HTTPException, Body
from app.weather.fusion import fusion_service
from app.alerts.alert_service import warning_service
from app.advisory.advisory_engine import advisory_engine
from app.schemas.advisory import SectorAdvisoryResponse, SectorAdvisoryRequest

router = APIRouter(prefix="/advisories", tags=["Sector Advisories"])


@router.get("", response_model=SectorAdvisoryResponse)
async def get_advisories(
    sector: str = Query("agriculture"),
    latitude: float = Query(17.3850, ge=-90, le=90),
    longitude: float = Query(78.4867, ge=-180, le=180),
    crop: str = Query("paddy")
):
    try:
        weather = await fusion_service.get_fused_weather(latitude, longitude, days=7)
        alerts = warning_service.get_alerts_for_location(latitude, longitude).alerts
        return advisory_engine.generate_advisory(sector, weather, alerts, {"crop": crop})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=SectorAdvisoryResponse)
async def generate_custom_advisory(req: SectorAdvisoryRequest):
    try:
        weather = await fusion_service.get_fused_weather(req.latitude, req.longitude, days=7)
        alerts = warning_service.get_alerts_for_location(req.latitude, req.longitude).alerts
        context = {"crop": req.crop, "activity": req.activity, "language": req.language}
        return advisory_engine.generate_advisory(req.sector, weather, alerts, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
