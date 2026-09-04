import re
from typing import Optional, List
from app.schemas.intent import QueryIntent, IntentType, UserRole, LocationTarget, TimeRange
from app.gis.geo_service import INDIAN_CITIES_REGISTRY
from app.core.logging import get_logger

logger = get_logger("ai.intent_parser")


class IntentParser:
    def detect_language(self, text: str) -> str:
        # Check Unicode script ranges
        for char in text:
            cp = ord(char)
            if 0x0C00 <= cp <= 0x0C7F:
                return "te"  # Telugu
            elif 0x0900 <= cp <= 0x097F:
                # Could be Hindi or Marathi, default Hindi
                return "hi"
            elif 0x0B80 <= cp <= 0x0BFF:
                return "ta"  # Tamil
            elif 0x0C80 <= cp <= 0x0CFF:
                return "kn"  # Kannada
            elif 0x0D00 <= cp <= 0x0D7F:
                return "ml"  # Malayalam
            elif 0x0980 <= cp <= 0x09FF:
                return "bn"  # Bengali
        return "en"

    def parse(
        self, query: str, default_lat: float = 17.3850, default_lon: float = 78.4867, default_loc_name: str = "Hyderabad",
        user_role_hint: Optional[str] = None, lang_hint: Optional[str] = None
    ) -> QueryIntent:
        q_lower = query.lower()
        detected_lang = lang_hint or self.detect_language(query)

        # 1. Location extraction
        target_loc = None
        for city in INDIAN_CITIES_REGISTRY:
            pattern = rf"\b{city['name'].lower()}\b"
            if re.search(pattern, q_lower):
                target_loc = LocationTarget(
                    name=city["name"],
                    latitude=city["latitude"],
                    longitude=city["longitude"]
                )
                break

        if not target_loc:
            target_loc = LocationTarget(
                name=default_loc_name,
                latitude=default_lat,
                longitude=default_lon
            )

        # 2. Time extraction
        rel_day = "today"
        if any(w in q_lower for w in ["tomorrow", "kal", "రేపు", "நாளை", "நாளைக்கு", "ನಾಳೆ", "நாಳೆ"]):
            rel_day = "tomorrow"
        elif any(w in q_lower for w in ["yesterday", "ninna", "కల్", "నిన్న"]):
            rel_day = "yesterday"
        elif any(w in q_lower for w in ["next week", "7 days", "last 7 days", "last week", "trend", "గత వారం"]):
            rel_day = "7_days"
        elif any(w in q_lower for w in ["forecast", "weekly", "next 5 days"]):
            rel_day = "forecast"

        time_range = TimeRange(relative_day=rel_day)

        # 3. User role & Crop detection
        role = UserRole.CITIZEN
        if user_role_hint:
            try:
                role = UserRole(user_role_hint.lower())
            except Exception:
                pass

        crop = None
        for c in ["paddy", "rice", "wheat", "cotton", "sugarcane", "maize", "chilli", "tomato"]:
            if c in q_lower:
                crop = c
                role = UserRole.FARMER
                break

        if any(w in q_lower for w in ["irrigate", "irrigation", "spray", "pesticide", "fertilizer", "crop", "field", "sow", "harvest", "వరి", "పంట", "రైతు", "छिड़काव", "सिंचाई"]):
            role = UserRole.FARMER

        # 4. Intent classification
        intent = IntentType.CURRENT_WEATHER

        if any(w in q_lower for w in ["trend", "last 7 days", "last week", "history", "historical", "గత 7 రోజులు", "గత వారం"]):
            intent = IntentType.HISTORICAL_WEATHER
        elif any(w in q_lower for w in ["climate", "anomaly", "compare"]):
            intent = IntentType.CLIMATE_TREND
        elif any(w in q_lower for w in ["irrigate", "irrigation", "spray", "pesticide", "crop", "farming", "agriculture", "వరి", "నీరు పెట్టవచ్చా", "పురుగుమందు"]):
            intent = IntentType.AGRICULTURE_ADVISORY
        elif any(w in q_lower for w in ["warning", "alert", "danger", "cyclone", "flood", "severe", "హెచ్చరిక", "ప్రమాదం", "चेतावनी"]):
            intent = IntentType.WARNING
        elif any(w in q_lower for w in ["travel", "drive", "commute", "road", "safe to travel", "flight", "trip"]):
            intent = IntentType.TRAVEL_ADVISORY
        elif any(w in q_lower for w in ["fisherman", "marine", "boat", "sea", "coastal"]):
            intent = IntentType.MARINE_ADVISORY
        elif any(w in q_lower for w in ["drone", "aviation", "flight", "pilot"]):
            intent = IntentType.AVIATION_ADVISORY
        elif any(w in q_lower for w in ["rain", "raining", "rainfall", "shower", "వర్షం", "వాన", "बारिश"]):
            intent = IntentType.RAINFALL
        elif any(w in q_lower for w in ["temperature", "hot", "cold", "heat", "weather", "forecast", "tomorrow", "ఎండ", "వేడి"]):
            intent = IntentType.FORECAST if rel_day == "tomorrow" else IntentType.TEMPERATURE

        params: List[str] = []
        if intent in [IntentType.RAINFALL, IntentType.AGRICULTURE_ADVISORY]:
            params.append("rainfall")
        if intent in [IntentType.TEMPERATURE, IntentType.HEAT_RISK]:
            params.append("temperature")
        if intent == IntentType.WARNING:
            params.append("alerts")

        return QueryIntent(
            intent=intent,
            location=target_loc,
            time_range=time_range,
            parameters=params,
            crop=crop,
            user_type=role,
            language=detected_lang,
            raw_query=query,
            confidence=0.98
        )


intent_parser = IntentParser()
