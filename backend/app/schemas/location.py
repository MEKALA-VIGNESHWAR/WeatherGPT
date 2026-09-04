from typing import List, Optional
from pydantic import BaseModel


class GeocodingResult(BaseModel):
    name: str
    latitude: float
    longitude: float
    state: Optional[str] = None
    country: str = "India"
    display_name: str
    district: Optional[str] = None


class ReverseGeocodingRequest(BaseModel):
    latitude: float
    longitude: float


class LocationSearchResponse(BaseModel):
    query: str
    results: List[GeocodingResult]
