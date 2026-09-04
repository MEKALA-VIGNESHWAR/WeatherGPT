from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.weather.fusion import fusion_service
from app.alerts.alert_service import warning_service
from app.advisory.advisory_engine import advisory_engine
from app.schemas.advisory import SectorAdvisoryResponse, SectorAdvisoryRequest
from app.core.database import get_db
from app.models.models import AdvisoryRecord
from app.core.logging import get_logger

logger = get_logger("api.advisories")

router = APIRouter(prefix="/advisories", tags=["Sector Advisories"])


def _persist_advisory_record(db: Optional[Session], res: SectorAdvisoryResponse, crop: Optional[str]):
    if not db:
        return
    try:
        primary_rec = res.advisories[0] if res.advisories else None
        if not primary_rec:
            return
        rec = AdvisoryRecord(
            location=res.location,
            sector=res.sector,
            crop=crop,
            title=primary_rec.title,
            recommendation=primary_rec.recommendation,
            risk_level=primary_rec.risk_level,
            risk_score=primary_rec.risk_score,
            forecast_data=res.weather_basis,
            valid_until=primary_rec.valid_until
        )
        db.add(rec)
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist advisory record: {e}")
        try:
            db.rollback()
        except Exception:
            pass


@router.get("", response_model=SectorAdvisoryResponse)
async def get_advisories(
    sector: str = Query("agriculture"),
    latitude: float = Query(17.3850, ge=-90, le=90),
    longitude: float = Query(78.4867, ge=-180, le=180),
    crop: str = Query("paddy"),
    horizon_days: int = Query(1, ge=1, le=7),
    db: Session = Depends(get_db)
):
    try:
        weather = await fusion_service.get_fused_weather(latitude, longitude, days=7)
        alerts = warning_service.get_alerts_for_location(latitude, longitude).alerts
        context = {"crop": crop, "horizon_days": horizon_days}
        res = advisory_engine.generate_advisory(sector, weather, alerts, context)
        _persist_advisory_record(db, res, crop)
        return res
    except Exception as e:
        logger.error(f"Failed to generate sector advisory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=SectorAdvisoryResponse)
async def generate_custom_advisory(
    req: SectorAdvisoryRequest,
    db: Session = Depends(get_db)
):
    try:
        weather = await fusion_service.get_fused_weather(req.latitude, req.longitude, days=7)
        alerts = warning_service.get_alerts_for_location(req.latitude, req.longitude).alerts
        context = {
            "crop": req.crop,
            "activity": req.activity,
            "language": req.language,
            "horizon_days": req.horizon_days or 1
        }
        res = advisory_engine.generate_advisory(req.sector, weather, alerts, context)
        _persist_advisory_record(db, res, req.crop)
        return res
    except Exception as e:
        logger.error(f"Failed to generate custom advisory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
