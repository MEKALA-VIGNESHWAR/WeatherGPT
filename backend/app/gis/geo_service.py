import httpx
from typing import List, Optional, Dict, Any
from app.schemas.location import GeocodingResult, LocationSearchResponse
from app.core.cache import cache_service
from app.core.logging import get_logger

logger = get_logger("gis.geo_service")

# Pre-seeded Indian meteorological & major district locations for ultra-fast zero-latency offline resolution
INDIAN_CITIES_REGISTRY: List[Dict[str, Any]] = [
    {"name": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867, "district": "Hyderabad"},
    {"name": "Amaravati", "state": "Andhra Pradesh", "latitude": 16.5417, "longitude": 80.5158, "district": "Guntur"},
    {"name": "Visakhapatnam", "state": "Andhra Pradesh", "latitude": 17.6868, "longitude": 83.2185, "district": "Visakhapatnam"},
    {"name": "Vijayawada", "state": "Andhra Pradesh", "latitude": 16.5062, "longitude": 80.6480, "district": "NTR"},
    {"name": "Bengaluru", "state": "Karnataka", "latitude": 12.9716, "longitude": 77.5946, "district": "Bengaluru Urban"},
    {"name": "Chennai", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707, "district": "Chennai"},
    {"name": "Mumbai", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777, "district": "Mumbai City"},
    {"name": "Pune", "state": "Maharashtra", "latitude": 18.5204, "longitude": 73.8567, "district": "Pune"},
    {"name": "Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "district": "New Delhi"},
    {"name": "Kolkata", "state": "West Bengal", "latitude": 22.5726, "longitude": 88.3639, "district": "Kolkata"},
    {"name": "Thiruvananthapuram", "state": "Kerala", "latitude": 8.5241, "longitude": 76.9366, "district": "Thiruvananthapuram"},
    {"name": "Kochi", "state": "Kerala", "latitude": 9.9312, "longitude": 76.2673, "district": "Ernakulam"},
    {"name": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714, "district": "Ahmedabad"},
    {"name": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873, "district": "Jaipur"},
    {"name": "Lucknow", "state": "Uttar Pradesh", "latitude": 26.8467, "longitude": 80.9462, "district": "Lucknow"},
    {"name": "Bhopal", "state": "Madhya Pradesh", "latitude": 23.2599, "longitude": 77.4126, "district": "Bhopal"},
    {"name": "Patna", "state": "Bihar", "latitude": 25.5941, "longitude": 85.1376, "district": "Patna"},
    {"name": "Bhubaneswar", "state": "Odisha", "latitude": 20.2961, "longitude": 85.8245, "district": "Khordha"},
    {"name": "Puri", "state": "Odisha", "latitude": 19.8135, "longitude": 85.8312, "district": "Puri"},
    {"name": "Chandigarh", "state": "Punjab", "latitude": 30.7333, "longitude": 76.7794, "district": "Chandigarh"},
    {"name": "Warangal", "state": "Telangana", "latitude": 17.9689, "longitude": 79.5941, "district": "Warangal"},
    {"name": "Nizamabad", "state": "Telangana", "latitude": 18.6725, "longitude": 78.0941, "district": "Nizamabad"},
    {"name": "Coimbatore", "state": "Tamil Nadu", "latitude": 11.0168, "longitude": 76.9558, "district": "Coimbatore"}
]


class GeoService:
    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org"

    async def search_places(self, query: str) -> List[GeocodingResult]:
        query_clean = query.strip()
        if not query_clean:
            return []

        cache_key = f"geo:search:{query_clean.lower()}"
        cached = cache_service.get(cache_key)
        if cached:
            return [GeocodingResult.model_validate(c) for c in cached]

        results: List[GeocodingResult] = []

        # 1. Check local pre-seeded high precision Indian directory
        for item in INDIAN_CITIES_REGISTRY:
            if query_clean.lower() in item["name"].lower() or query_clean.lower() in item["state"].lower():
                results.append(
                    GeocodingResult(
                        name=item["name"],
                        latitude=item["latitude"],
                        longitude=item["longitude"],
                        state=item["state"],
                        country="India",
                        display_name=f"{item['name']}, {item['state']}, India",
                        district=item.get("district")
                    )
                )

        # 2. If not found or more needed, query OpenStreetMap Nominatim
        if not results:
            try:
                async with httpx.AsyncClient(headers={"User-Agent": "WeatherGPT-SIH2026/1.0"}, timeout=5.0) as client:
                    resp = await client.get(
                        f"{self.nominatim_url}/search",
                        params={"q": query_clean, "format": "json", "limit": 5, "countrycodes": "in"}
                    )
                    if resp.status_code == 200:
                        items = resp.json()
                        for it in items:
                            results.append(
                                GeocodingResult(
                                    name=it.get("name") or query_clean.title(),
                                    latitude=float(it["lat"]),
                                    longitude=float(it["lon"]),
                                    display_name=it.get("display_name", ""),
                                    country="India"
                                )
                            )
            except Exception as e:
                logger.warning(f"Nominatim lookup failed: {e}")

        # Fallback to Hyderabad if nothing found
        if not results:
            results.append(
                GeocodingResult(
                    name=query_clean.title(),
                    latitude=17.3850,
                    longitude=78.4867,
                    state="Telangana",
                    country="India",
                    display_name=f"{query_clean.title()} (Estimated Coordinates), India"
                )
            )

        cache_service.set(cache_key, [r.model_dump() for r in results], ttl_seconds=86400)
        return results

    async def reverse_geocode(self, latitude: float, longitude: float) -> GeocodingResult:
        cache_key = f"geo:rev:{round(latitude, 3)}:{round(longitude, 3)}"
        cached = cache_service.get(cache_key)
        if cached:
            return GeocodingResult.model_validate(cached)

        # Find closest city in our registry first
        closest = None
        min_dist = float("inf")
        for c in INDIAN_CITIES_REGISTRY:
            dist = (c["latitude"] - latitude) ** 2 + (c["longitude"] - longitude) ** 2
            if dist < min_dist:
                min_dist = dist
                closest = c

        if closest and min_dist < 0.05:  # within ~25 km
            res = GeocodingResult(
                name=closest["name"],
                latitude=latitude,
                longitude=longitude,
                state=closest["state"],
                country="India",
                display_name=f"{closest['name']}, {closest['state']}, India",
                district=closest.get("district")
            )
            cache_service.set(cache_key, res.model_dump(), ttl_seconds=86400)
            return res

        # Online reverse geocoding via bigdatacloud or nominatim
        try:
            url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    city = data.get("city") or data.get("locality") or "Detected Location"
                    state = data.get("principalSubdivision") or ""
                    country = data.get("countryName") or "India"
                    res = GeocodingResult(
                        name=city,
                        latitude=latitude,
                        longitude=longitude,
                        state=state,
                        country=country,
                        display_name=f"{city}, {state}, {country}".strip(", ")
                    )
                    cache_service.set(cache_key, res.model_dump(), ttl_seconds=86400)
                    return res
        except Exception as e:
            logger.warning(f"Reverse geocode lookup failed: {e}")

        # Fallback default
        res = GeocodingResult(
            name="Your Location",
            latitude=latitude,
            longitude=longitude,
            state="India",
            country="India",
            display_name="Your Location, India"
        )
        return res


geo_service = GeoService()
