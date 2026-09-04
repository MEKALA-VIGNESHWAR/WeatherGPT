from typing import Optional
from fastapi import APIRouter, Query
from app.alerts.alert_service import warning_service
from app.schemas.alert import ActiveAlertsResponse

router = APIRouter(prefix="/alerts", tags=["Alerts & Warnings"])


@router.get("/active", response_model=ActiveAlertsResponse)
async def get_active_alerts(
    latitude: float = Query(17.3850, ge=-90, le=90),
    longitude: float = Query(78.4867, ge=-180, le=180),
    location_name: Optional[str] = Query("Current Location")
):
    return warning_service.get_alerts_for_location(latitude, longitude, location_name=location_name)


@router.get("", response_model=ActiveAlertsResponse)
async def list_all_alerts():
    # Return all known active bulletins
    return warning_service.get_alerts_for_location(17.3850, 78.4867, location_name="Pan-India Watch")
