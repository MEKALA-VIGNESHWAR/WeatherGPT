from fastapi import APIRouter
from app.gis.geo_service import INDIAN_CITIES_REGISTRY
from app.alerts.alert_service import warning_service

router = APIRouter(prefix="/map", tags=["GIS & Map Layers"])


@router.get("/layers")
async def get_map_layers():
    """
    Returns available raster/vector GIS layers and active spatial points for MapLibre/Leaflet.
    """
    alerts = warning_service._regional_bulletins
    
    # GeoJSON FeatureCollection for active warning hazard zones
    hazard_features = []
    for a in alerts:
        if a.latitude and a.longitude:
            hazard_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [a.longitude, a.latitude]
                },
                "properties": {
                    "id": a.id,
                    "headline": a.headline,
                    "severity": a.severity.value,
                    "color": a.color_code,
                    "radius_km": a.radius_km or 100,
                    "instruction": a.instruction
                }
            })

    # Weather station points across India
    station_features = []
    for c in INDIAN_CITIES_REGISTRY:
        station_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [c["longitude"], c["latitude"]]
            },
            "properties": {
                "name": c["name"],
                "state": c["state"],
                "district": c.get("district")
            }
        })

    return {
        "base_tiles": {
            "name": "OpenStreetMap Standard",
            "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": "&copy; OpenStreetMap contributors"
        },
        "overlay_layers": [
            {
                "id": "precipitation",
                "title": "Precipitation Radar / Forecast",
                "type": "tile",
                "url": "https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png",
                "opacity": 0.65
            },
            {
                "id": "temperature",
                "title": "Thermal Isotherms",
                "type": "tile",
                "url": "https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png",
                "opacity": 0.55
            },
            {
                "id": "wind",
                "title": "Wind Velocity Vectors",
                "type": "tile",
                "url": "https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png",
                "opacity": 0.55
            }
        ],
        "hazard_zones": {
            "type": "FeatureCollection",
            "features": hazard_features
        },
        "station_points": {
            "type": "FeatureCollection",
            "features": station_features
        }
    }
