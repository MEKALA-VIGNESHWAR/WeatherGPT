from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SectorAdvisoryRequest(BaseModel):
    sector: str  # agriculture, disaster, citizen, marine, aviation
    latitude: float
    longitude: float
    crop: Optional[str] = None
    activity: Optional[str] = None
    language: Optional[str] = "en"
    horizon_days: Optional[int] = 1


class SectorAdvisoryItem(BaseModel):
    sector: str
    location: str
    crop: Optional[str] = None
    title: str
    recommendation: str  # DELAY_IRRIGATION, SAFE_TO_IRRIGATE, NOT_RECOMMENDED, POSTPONE, FAVORABLE, ELEVATED_RISK, etc.
    icon: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: float = Field(default=0.0, description="0-100 explainable risk score")
    risk_factors: List[str] = Field(default_factory=list)
    weather_trigger: Dict[str, Any] = Field(default_factory=dict)
    basis: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    avoid_actions: List[str] = Field(default_factory=list)
    valid_from: str
    valid_until: str
    sources: List[str] = Field(default_factory=lambda: ["Open-Meteo forecast"])
    confidence: str = "Based on current forecast data"
    limitations: List[str] = Field(default_factory=list)
    horizon_breakdown: Optional[List[Dict[str, Any]]] = None


# Backward-compatible alias for existing imports
AdvisoryRecommendation = SectorAdvisoryItem


class SectorAdvisoryResponse(BaseModel):
    location: str
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    sector: str
    overall_risk: str
    overall_risk_score: float = 0.0
    advisories: List[SectorAdvisoryItem]
    recommendations: List[SectorAdvisoryItem] = Field(default_factory=list, description="Backward compatibility alias")
    weather_basis: Dict[str, Any] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=lambda: ["Open-Meteo forecast"])
    generated_at: str
    official_alerts: List[Dict[str, Any]] = Field(default_factory=list)
