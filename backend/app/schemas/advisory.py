from typing import List, Optional
from pydantic import BaseModel, Field


class SectorAdvisoryRequest(BaseModel):
    sector: str  # agriculture, disaster, travel, aviation, marine, urban, research
    latitude: float
    longitude: float
    crop: Optional[str] = None
    activity: Optional[str] = None
    language: Optional[str] = "en"


class AdvisoryRecommendation(BaseModel):
    title: str
    verdict: str  # SAFE, ADVISABLE, CAUTION, NOT_RECOMMENDED, HAZARD
    icon: str
    summary: str
    reasons: List[str]
    actionable_steps: List[str]
    valid_until: str
    sector: str


class SectorAdvisoryResponse(BaseModel):
    location: str
    sector: str
    overall_risk: str
    recommendations: List[AdvisoryRecommendation]
    weather_basis: dict
    source: str
    generated_at: str
