from fastapi import APIRouter, Query
from app.gis.geo_service import geo_service
from app.schemas.location import LocationSearchResponse, GeocodingResult

router = APIRouter(prefix="/locations", tags=["Geocoding & Locations"])


@router.get("/search", response_model=LocationSearchResponse)
async def search_locations(q: str = Query(..., min_length=1)):
    results = await geo_service.search_places(q)
    return LocationSearchResponse(query=q, results=results)


@router.get("/reverse", response_model=GeocodingResult)
async def reverse_geocode(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    return await geo_service.reverse_geocode(latitude, longitude)
