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
        candidate_loc_name = None

        # Common global cities for instant resolution
        GLOBAL_CITIES_MAP = {
            "london": ("London", 51.5085, -0.1257, "England", "United Kingdom"),
            "new york": ("New York", 40.7143, -74.0060, "New York", "United States"),
            "paris": ("Paris", 48.8534, 2.3488, "Ile-de-France", "France"),
            "tokyo": ("Tokyo", 35.6895, 139.6917, "Tokyo", "Japan"),
            "dubai": ("Dubai", 25.0772, 55.3093, "Dubai", "United Arab Emirates"),
            "singapore": ("Singapore", 1.2897, 103.8501, "Central", "Singapore"),
            "sydney": ("Sydney", -33.8678, 151.2073, "New South Wales", "Australia"),
            "toronto": ("Toronto", 43.7001, -79.4163, "Ontario", "Canada"),
            "berlin": ("Berlin", 52.5244, 13.4105, "Berlin", "Germany")
        }

        # 1. Multi-Location Extraction & Route Detection
        matched_locations: List[LocationTarget] = []
        candidate_loc_names: List[str] = []
        seen_city_names = set()
        origin_loc: Optional[LocationTarget] = None
        dest_loc: Optional[LocationTarget] = None

        # Check for route pattern: "from X to Y"
        route_pattern = r"\bfrom\s+([a-zA-Z\s]{2,25}?)\s+to\s+([a-zA-Z\s]{2,25}?)(?:\s*(?:today|tomorrow|yesterday|now|\?|\.|$))"
        route_m = re.search(route_pattern, query, re.I)
        from_name = None
        to_name = None
        if route_m:
            from_name = route_m.group(1).strip()
            to_name = route_m.group(2).strip()

        # Check local registry with aliases (supports both English and Indic scripts)
        for city in INDIAN_CITIES_REGISTRY:
            c_name = city["name"]
            aliases = city.get("aliases", [c_name.lower()])
            for a in aliases:
                a_lower = a.lower()
                # word-boundary or substring check
                if re.search(r'\b' + re.escape(a_lower) + r'\b', q_lower) or (len(a_lower) > 4 and a_lower in q_lower):
                    if c_name.lower() not in seen_city_names:
                        loc_obj = LocationTarget(
                            name=c_name,
                            latitude=city["latitude"],
                            longitude=city["longitude"],
                            state=city.get("state"),
                            country="India"
                        )
                        matched_locations.append(loc_obj)
                        seen_city_names.add(c_name.lower())
                        if from_name and any(a.lower() in from_name.lower() or from_name.lower() in a.lower() for a in aliases):
                            origin_loc = loc_obj
                        if to_name and any(a.lower() in to_name.lower() or to_name.lower() in a.lower() for a in aliases):
                            dest_loc = loc_obj
                    break

        # Check global cities
        for g_key, (g_name, g_lat, g_lon, g_state, g_country) in GLOBAL_CITIES_MAP.items():
            if re.search(r'\b' + re.escape(g_key) + r'\b', q_lower):
                if g_name.lower() not in seen_city_names:
                    loc_obj = LocationTarget(
                        name=g_name,
                        latitude=g_lat,
                        longitude=g_lon,
                        state=g_state,
                        country=g_country
                    )
                    matched_locations.append(loc_obj)
                    seen_city_names.add(g_name.lower())
                    if from_name and (g_name.lower() in from_name.lower() or from_name.lower() in g_name.lower() or g_key.lower() in from_name.lower()):
                        origin_loc = loc_obj
                    if to_name and (g_name.lower() in to_name.lower() or to_name.lower() in g_name.lower() or g_key.lower() in to_name.lower()):
                        dest_loc = loc_obj

        # Check prepositional patterns if no predefined match or for additional candidate names
        patterns = [
            r"\b(?:in|at|for|near|around|to)\s+([a-zA-Z\s]{2,30}?)(?:\s*(?:today|tomorrow|yesterday|this\s+week|now|\d{1,2}\s*(?:am|pm)|\?|\.|$))",
            r"weather\s+(?:in|for|at|around)\s+([a-zA-Z\s]{2,30}?)(?:\s*(?:today|tomorrow|\?|\.|$))",
        ]
        excluded_phrases = {
            "today", "tomorrow", "yesterday", "now", "this week", "next week", "an umbrella", "umbrella",
            "my field", "my crop", "cotton crop", "paddy field", "pesticides", "pesticide", "outdoor activity",
            "outdoor activities", "two wheeler", "two-wheeler", "bike", "car", "morning", "evening", "night",
            "6 pm", "6pm", "6 am", "6am", "rain", "raining", "rainfall", "shower", "showers", "drizzle",
            "precipitation", "thunderstorm", "weather", "forecast", "climate", "wind", "humidity",
            "temp", "temperature", "heat", "cold", "clouds", "sun", "few days", "next days", "the next",
            "next 4 days", "4 days", "weekend", "week", "these few days"
        }
        for p in patterns:
            for m in re.finditer(p, query, re.IGNORECASE):
                cand = m.group(1).strip().strip("?.!,")
                cand_clean = re.sub(r"^(?:an|a|the)\s+", "", cand, flags=re.I).strip()
                if (
                    cand.lower() not in excluded_phrases
                    and cand_clean.lower() not in excluded_phrases
                    and cand_clean.lower() not in seen_city_names
                    and not re.match(r"^\d{1,2}\s*(?:am|pm)?$", cand.lower())
                ):
                    candidate_loc_names.append(cand_clean)
                    seen_city_names.add(cand_clean.lower())

        target_loc = matched_locations[0] if matched_locations else None
        candidate_loc_name = candidate_loc_names[0] if candidate_loc_names else None

        # Fallback to default user location only if NO location was mentioned anywhere in query
        if not target_loc and not candidate_loc_names:
            target_loc = LocationTarget(
                name=default_loc_name,
                latitude=default_lat,
                longitude=default_lon
            )
            matched_locations.append(target_loc)

        # 2. Time extraction & Horizon Detection
        rel_day = "today"
        horizon_days = 1
        day_offset = 0
        hour_start = None
        hour_end = None

        # Check for multi-day horizons
        m_days = re.search(r"\b(?:next|within|up to|in)\s+(\d{1,2})\s+days\b", q_lower)
        if not m_days:
            m_days = re.search(r"\b(\d{1,2})\s+days\b", q_lower)
        
        if any(w in q_lower for w in ["up to 4 days", "next 4 days", "4 days", "four days", "few days like up to 4 days"]):
            rel_day = "next_4_days"
            horizon_days = 4
            day_offset = 0
        elif any(w in q_lower for w in ["next 3 days", "3 days", "three days"]):
            rel_day = "next_3_days"
            horizon_days = 3
            day_offset = 0
        elif any(w in q_lower for w in ["next 2 days", "2 days", "two days"]):
            rel_day = "next_2_days"
            horizon_days = 2
            day_offset = 0
        elif any(w in q_lower for w in ["next 5 days", "5 days", "five days"]):
            rel_day = "next_5_days"
            horizon_days = 5
            day_offset = 0
        elif any(w in q_lower for w in ["next 7 days", "7 days", "seven days", "this week", "next week", "weekly", "trend", "last 7 days"]):
            rel_day = "next_7_days"
            horizon_days = 7
            day_offset = 0
        elif m_days:
            num = int(m_days.group(1))
            if 1 <= num <= 7:
                horizon_days = num
                rel_day = f"next_{num}_days"
                day_offset = 0
        elif any(w in q_lower for w in ["which day", "when is rain", "when will it rain", "best day"]):
            rel_day = "next_4_days"
            horizon_days = 4
            day_offset = 0
        elif "weekend" in q_lower:
            rel_day = "weekend"
            horizon_days = 2
            day_offset = 1
        elif "tomorrow evening" in q_lower:
            rel_day = "tomorrow_evening"
            horizon_days = 1
            day_offset = 1
            hour_start = 17
            hour_end = 21
        elif "tomorrow morning" in q_lower:
            rel_day = "tomorrow_morning"
            horizon_days = 1
            day_offset = 1
            hour_start = 6
            hour_end = 11
        elif "tomorrow afternoon" in q_lower:
            rel_day = "tomorrow_afternoon"
            horizon_days = 1
            day_offset = 1
            hour_start = 12
            hour_end = 16
        elif "tomorrow night" in q_lower:
            rel_day = "tomorrow_night"
            horizon_days = 1
            day_offset = 1
            hour_start = 20
            hour_end = 23
        elif any(w in q_lower for w in ["tomorrow", "kal", "రేపు", "நாளை", "நாளைக்கு", "ನಾಳೆ", "நாಳೆ"]):
            rel_day = "tomorrow"
            horizon_days = 1
            day_offset = 1
        elif "tonight" in q_lower:
            rel_day = "tonight"
            horizon_days = 1
            day_offset = 0
            hour_start = 20
            hour_end = 23
        elif any(w in q_lower for w in ["yesterday", "ninna", "కల్", "నిన్న"]):
            rel_day = "yesterday"
            horizon_days = 1
            day_offset = -1

        # Specific target hour extraction (e.g. "6 PM", "6pm", "18:00")
        target_hour = None
        hour_match = re.search(r"\b(\d{1,2})\s*(am|pm)\b", q_lower)
        if hour_match:
            hr = int(hour_match.group(1))
            meridiem = hour_match.group(2)
            if meridiem == "pm" and hr < 12:
                hr += 12
            elif meridiem == "am" and hr == 12:
                hr = 0
            if 0 <= hr <= 23:
                target_hour = hr
        else:
            mil_match = re.search(r"\b([01]?\d|2[0-3]):00\b", q_lower)
            if mil_match:
                target_hour = int(mil_match.group(1))

        time_range = TimeRange(
            relative_day=rel_day,
            target_hour=target_hour,
            hour_start=hour_start,
            hour_end=hour_end,
            horizon_days=horizon_days,
            day_offset=day_offset
        )

        # 3. User role & Crop detection
        role = UserRole.CITIZEN
        if user_role_hint:
            try:
                role = UserRole(user_role_hint.lower())
            except Exception:
                pass

        crop = None
        crop_aliases = {
            "paddy": ["paddy", "rice", "dhan", "వరి", "धान", "நெல்"],
            "cotton": ["cotton", "kapas", "పత్తి", "कपास", "பருத்தி"],
            "wheat": ["wheat", "gehun", "గోధుమ", "गेहूं", "கோதுமை"],
            "sugarcane": ["sugarcane", "ganna", "చెరకు", "गन्ना", "கரும்பு"],
            "chilli": ["chilli", "spices", "mirchi", "మిరప", "मिर्च", "மிளகாய்"]
        }
        for c_key, aliases in crop_aliases.items():
            if any(a in q_lower for a in aliases):
                crop = c_key
                role = UserRole.FARMER
                break

        if any(w in q_lower for w in ["irrigate", "irrigation", "spray", "pesticide", "fertilizer", "crop", "field", "sow", "harvest", "వరి", "పంట", "రైతు", "छिड़काव", "सिंचाई"]):
            role = UserRole.FARMER

        # 4. Weather Variable & Question Focus Detection
        weather_variable = "general"
        if any(w in q_lower for w in ["umbrella", "గొడుగు", "छाता"]):
            weather_variable = "umbrella"
        elif any(w in q_lower for w in ["rain", "raining", "rainfall", "shower", "showers", "drizzle", "precipitation", "wet", "వర్షం", "వాన", "बारिश", "மழை"]):
            weather_variable = "rain"
        elif any(w in q_lower for w in ["outdoor", "outdoors", "picnic", "trip", "activity", "activities", "safest option"]):
            weather_variable = "outdoor"
        elif any(w in q_lower for w in ["temperature", "temp", "hot", "cold", "heat", "warm", "hotter", "cooler", "degree", "celsius", "వేడి", "చలి", "तापमान"]):
            weather_variable = "temperature"
        elif any(w in q_lower for w in ["wind", "windy", "breeze", "gust", "గాలి", "हवा"]):
            weather_variable = "wind"
        elif any(w in q_lower for w in ["humidity", "humid", "muggy", "తేమ", "नमी"]):
            weather_variable = "humidity"

        question_focus = "general_weather"
        if any(w in q_lower for w in ["irrigate", "irrigation", "water my", "watering", "నీరు పెట్టవచ్చా", "सिंचाई"]):
            question_focus = "irrigation"
        elif any(w in q_lower for w in ["spray", "spraying", "pesticide", "fungicide", "foliar", "పురుగుమందు", "छिड़काव"]):
            question_focus = "spraying"
        elif crop and (horizon_days > 1 or any(w in q_lower for w in ["4 days", "few days", "next days", "week"])):
            question_focus = "agriculture_multi_day"
        elif crop and any(w in q_lower for w in ["what should i do", "advice", "advisory", "care", "risks"]):
            question_focus = "agriculture_general"
        elif weather_variable == "umbrella":
            question_focus = "carry_umbrella"
        elif any(w in q_lower for w in ["outdoor", "outdoors", "picnic", "safest option", "best day to avoid rain", "best day for an outdoor", "best day"]):
            question_focus = "best_outdoor_day"
        elif any(w in q_lower for w in ["when will it rain", "when is rain", "what time", "which day has the highest", "which day will have rain", "peak", "highest chance"]):
            question_focus = "peak_rain_time"
        elif any(w in q_lower for w in ["compare", "difference", "vs"]) and ("rain" in q_lower or "precipitation" in q_lower):
            question_focus = "compare_rain"
        elif ("hotter" in q_lower or "cooler" in q_lower) or (any(w in q_lower for w in ["vs", "compare", "difference"]) and any(w in q_lower for w in ["temp", "temperature", "hot"])):
            question_focus = "compare_temperature"
        elif any(w in q_lower for w in ["will it rain", "chance of rain", "is there any chance of rain", "is it raining", "any rain", "rain expected", "rain possible"]):
            question_focus = "rain_possibility"
        elif any(w in q_lower for w in ["how hot", "how cold", "what is the temperature", "high temp"]):
            question_focus = "temperature_forecast"
        elif any(w in q_lower for w in ["what's the weather", "what is the weather", "weather forecast", "how is the weather"]):
            question_focus = "general_forecast"

        # 5. Intent classification
        intent = IntentType.CURRENT_WEATHER

        # 5. Relational Goal, Comparison Criteria & Activity Extraction
        relational_goal = None
        if any(w in q_lower for w in ["why", "reason", "cause", "explain why", "ఎందుకు", "क्यों"]):
            relational_goal = "why_explanation"
        elif any(w in q_lower for w in ["best", "safest", "top", "favorable", "preferable", "good time"]):
            relational_goal = "best"
        elif any(w in q_lower for w in ["worst", "avoid", "bad", "hazard", "hazardous", "danger", "risk"]):
            relational_goal = "avoid"
        elif any(w in q_lower for w in ["should i", "recommend", "advice", "suggest", "is it good", "feasible"]):
            relational_goal = "recommendation"
        elif any(w in q_lower for w in ["compare", "vs", "versus", "warmer", "cooler", "hotter", "colder", "difference"]):
            relational_goal = "compare"

        comparison_criteria = "overall"
        if any(w in q_lower for w in ["hotter", "cooler", "warmer", "colder", "temp", "temperature", "heat", "cold"]):
            comparison_criteria = "temperature"
        elif any(w in q_lower for w in ["rain", "rainier", "wetter", "drier", "dry", "rainfall", "precipitation"]):
            comparison_criteria = "rain"
        elif any(w in q_lower for w in ["wind", "windy", "breeze", "squall"]):
            comparison_criteria = "wind"
        elif any(w in q_lower for w in ["humid", "humidity"]):
            comparison_criteria = "humidity"

        activity = None
        if any(w in q_lower for w in ["driving", "drive", "road trip", "commute", "travel from", "highway", "car", "bike"]):
            activity = "driving"
        elif any(w in q_lower for w in ["cricket", "sports", "match", "game", "football"]):
            activity = "sports"
        elif any(w in q_lower for w in ["outdoor", "picnic", "event", "wedding", "walk", "jogging"]):
            activity = "outdoor"
        elif any(w in q_lower for w in ["drone", "uav", "flight", "pilot"]):
            activity = "drone"
        elif any(w in q_lower for w in ["crop", "irrigate", "spray", "farming", "paddy", "cotton"]):
            activity = "farming"

        # 6. Intent classification
        intent = IntentType.CURRENT_WEATHER

        if len(matched_locations) >= 2 or route_m:
            intent = IntentType.COMPARISON
            question_focus = "compare_locations"
            if not relational_goal:
                relational_goal = "compare"
        elif question_focus in ["compare_rain", "compare_temperature"] or any(w in q_lower for w in ["vs", "compare", "difference between"]):
            intent = IntentType.COMPARISON
        elif any(w in q_lower for w in ["trend", "last 7 days", "last week", "history", "historical", "గత 7 రోజులు", "గత వారం"]):
            intent = IntentType.HISTORICAL_WEATHER
        elif any(w in q_lower for w in ["climate", "anomaly"]):
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
        elif weather_variable in ["rain", "umbrella"]:
            intent = IntentType.RAINFALL
        elif weather_variable == "temperature":
            intent = IntentType.FORECAST if rel_day != "today" else IntentType.TEMPERATURE
        elif horizon_days > 1 or rel_day in ["tomorrow", "weekend", "forecast"]:
            intent = IntentType.FORECAST
        else:
            # Check if this query is totally unrelated to weather/meteorology
            weather_vocab = [
                "weather", "forecast", "climate", "rain", "temperature", "humidity", "wind", "cloud",
                "sun", "sunny", "storm", "cyclone", "flood", "temp", "degree", "celsius", "hot", "cold",
                "air", "sky", "umbrella", "alert", "warning", "monsoon", "drought", "breeze", "uv",
                "atmosphere", "pressure", "barometer", "precipitation", "outdoor", "picnic"
            ]
            has_weather_term = any(w in q_lower for w in weather_vocab)
            if not has_weather_term and not target_loc:
                intent = IntentType.GENERAL_QUESTION

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
            confidence=0.98,
            candidate_location=candidate_loc_name,
            locations=matched_locations,
            candidate_locations=candidate_loc_names,
            origin_location=origin_loc,
            destination_location=dest_loc,
            comparison_criteria=comparison_criteria,
            relational_goal=relational_goal,
            activity=activity,
            weather_variable=weather_variable,
            question_focus=question_focus
        )


intent_parser = IntentParser()
