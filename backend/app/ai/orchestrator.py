import uuid
import time
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.ai.intent_parser import intent_parser
from app.ai.tools import weather_tools
from app.ai.llm_provider import get_llm_provider, GroundedRuleLLMProvider
from app.ai.translations import get_translated_string
from app.ai.rag_service import rag_service
from app.gis.geo_service import geo_service
from app.weather.analysis import weather_analyzer
from app.advisory.advisory_engine import advisory_engine
from app.schemas.chat import (
    ChatRequest, ChatResponse, WeatherSummary, RiskLevel, AdvisoryItem, ToolCallTrace
)
from app.schemas.intent import IntentType, UserRole, LocationTarget
from app.schemas.alert import WeatherAlert, AlertSeverity
from app.core.logging import get_logger

logger = get_logger("ai.orchestrator")


class WeatherIntelligenceOrchestrator:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    async def process_query(self, req: ChatRequest) -> ChatResponse:
        t_start = time.time()
        conv_id = req.conversation_id or str(uuid.uuid4())
        msg_id = str(uuid.uuid4())
        tools_called: List[ToolCallTrace] = []

        logger.info(f"[USER QUERY] text: '{req.message}', user_role: {req.user_role}, language: {req.language}")

        # 1. Query Understanding & Intent Parsing
        intent_obj = intent_parser.parse(
            query=req.message,
            default_lat=req.latitude or 17.3850,
            default_lon=req.longitude or 78.4867,
            default_loc_name=req.location_name or "Hyderabad",
            user_role_hint=req.user_role,
            lang_hint=req.language
        )
        lang = intent_obj.language or req.language or "en"

        # 2. Check for Unrelated / General Knowledge Queries
        if intent_obj.intent == IntentType.GENERAL_QUESTION:
            logger.info(f"[GENERAL QUESTION] query: '{req.message}'")
            system_prompt = (
                "You are WeatherGPT, an AI meteorological intelligence assistant. "
                "The user asked a general question unrelated to weather or agriculture. "
                "Answer their question concisely and accurately (1-2 sentences), and politely remind them "
                "that you specialize in real-time weather forecasts, alerts, and agricultural decision support."
            )
            general_answer = "I am WeatherGPT, specialized in weather intelligence and forecasts."
            try:
                ai_resp = await self.llm_provider.generate_response(system_prompt, req.message)
                if ai_resp and len(ai_resp.strip()) > 5:
                    general_answer = ai_resp.strip()
            except Exception as e:
                logger.warning(f"Failed to generate general question response: {e}")

            return ChatResponse(
                conversation_id=conv_id,
                message_id=msg_id,
                answer=general_answer,
                location=req.location_name or "General",
                time_range="N/A",
                weather_summary=None,
                risk_level=RiskLevel.LOW,
                advisories=[],
                warnings=[],
                sources=["WeatherGPT Intelligence Engine"],
                updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                confidence="Based on current forecast data",
                tools_called=[],
                language=lang
            )

        # 3. Location Resolution (Single or Multi-Location)
        loc_targets: List[LocationTarget] = []
        if intent_obj.origin_location and intent_obj.destination_location:
            loc_targets = [intent_obj.origin_location, intent_obj.destination_location]
        elif intent_obj.locations and len(intent_obj.locations) > 1:
            loc_targets = list(intent_obj.locations)
        elif intent_obj.candidate_locations and len(intent_obj.candidate_locations) > 1:
            for c_loc in intent_obj.candidate_locations:
                geo_res = await geo_service.search_places(c_loc)
                if geo_res:
                    loc_targets.append(LocationTarget(name=geo_res[0].name, latitude=geo_res[0].latitude, longitude=geo_res[0].longitude))

        # Check if this is a Multi-Location comparison / route query
        is_multi_loc = len(loc_targets) >= 2
        weather_data = None
        alerts_list: List[WeatherAlert] = []
        target_name = None
        target_lat = None
        target_lon = None

        if is_multi_loc:
            logger.info(f"[MULTI-LOCATION] Processing {len(loc_targets)} locations: {[lt.name for lt in loc_targets]}")
            t_mult0 = time.time()
            forecast_tasks = [weather_tools.get_forecast(lt.latitude, lt.longitude, days=7) for lt in loc_targets]
            alert_tasks = [weather_tools.get_active_alerts(lt.latitude, lt.longitude, location_name=lt.name) for lt in loc_targets]

            weathers = await asyncio.gather(*forecast_tasks)
            alert_resps = await asyncio.gather(*alert_tasks)
            elapsed_mult = round((time.time() - t_mult0) * 1000, 1)

            for lt in loc_targets:
                tools_called.append(
                    ToolCallTrace(
                        tool_name="get_forecast",
                        arguments={"location": lt.name, "latitude": lt.latitude, "longitude": lt.longitude},
                        execution_time_ms=round(elapsed_mult / len(loc_targets), 1)
                    )
                )

            for a_resp in alert_resps:
                alerts_list.extend(a_resp.alerts)

            weather_map = {}
            for lt, w in zip(loc_targets, weathers):
                w.location.name = lt.name
                weather_map[lt.name] = w

            multi_analysis = weather_analyzer.analyze_multi_locations(weather_map, intent_obj)
            analysis = weather_analyzer.analyze(weathers[0], intent_obj)
            analysis.multi_location = multi_analysis

            weather_data = weathers[0]
            if intent_obj.origin_location and intent_obj.destination_location:
                target_name = f"{intent_obj.origin_location.name} to {intent_obj.destination_location.name}"
            else:
                target_name = " vs ".join([lt.name for lt in loc_targets])
            target_lat = loc_targets[0].latitude
            target_lon = loc_targets[0].longitude
        else:
            # Single Location Flow
            if intent_obj.candidate_location and not intent_obj.location:
                logger.info(f"[GEO SEARCH] searching candidate location: '{intent_obj.candidate_location}'")
                geo_results = await geo_service.search_places(intent_obj.candidate_location)
                if geo_results:
                    target_lat = geo_results[0].latitude
                    target_lon = geo_results[0].longitude
                    target_name = geo_results[0].name
                    logger.info(f"[LOCATION RESOLUTION] resolved '{intent_obj.candidate_location}' -> '{target_name}' ({target_lat}, {target_lon})")
                else:
                    logger.warning(f"[LOCATION RESOLUTION FAILED] candidate: '{intent_obj.candidate_location}' could not be resolved.")
                    err_msg = (
                        f"Could not find a location matching '{intent_obj.candidate_location}'. "
                        "Please check the spelling or provide a more specific location (such as city, state, or country)."
                    )
                    return ChatResponse(
                        conversation_id=conv_id,
                        message_id=msg_id,
                        answer=err_msg,
                        location=intent_obj.candidate_location,
                        time_range="N/A",
                        weather_summary=None,
                        risk_level=RiskLevel.LOW,
                        advisories=[],
                        warnings=[],
                        sources=["Open-Meteo Geocoding"],
                        updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                        confidence="Based on current forecast data",
                        tools_called=[],
                        language=lang
                    )
            elif intent_obj.location:
                target_lat = intent_obj.location.latitude
                target_lon = intent_obj.location.longitude
                target_name = intent_obj.location.name
            elif req.latitude and req.longitude:
                target_lat = req.latitude
                target_lon = req.longitude
                target_name = req.location_name or "Your Location"
            else:
                target_lat = 17.3850
                target_lon = 78.4867
                target_name = "Hyderabad"

            logger.info(f"[LOCATION RESOLUTION] final target: '{target_name}' at ({target_lat:.4f}, {target_lon:.4f})")

            # 4. Tool Execution (Verified Open-Meteo Data Retrieval)
            tool_t0 = time.time()
            logger.info(f"[OPEN-METEO REQUEST] fetching forecast for lat={target_lat}, lon={target_lon}")
            weather_data = await weather_tools.get_forecast(target_lat, target_lon, days=7)
            tools_called.append(
                ToolCallTrace(
                    tool_name="get_forecast",
                    arguments={"latitude": target_lat, "longitude": target_lon, "days": 7},
                    execution_time_ms=round((time.time() - tool_t0) * 1000, 1)
                )
            )
            logger.info(f"[OPEN-METEO RESPONSE STATUS] status: 200, points: {len(weather_data.hourly)}")

            tool_t1 = time.time()
            active_alerts_resp = await weather_tools.get_active_alerts(target_lat, target_lon, location_name=target_name)
            tools_called.append(
                ToolCallTrace(
                    tool_name="get_active_alerts",
                    arguments={"latitude": target_lat, "longitude": target_lon},
                    execution_time_ms=round((time.time() - tool_t1) * 1000, 1)
                )
            )
            alerts_list = active_alerts_resp.alerts

            # 5. Backend Statistical & Numerical Analysis (BEFORE Gemini)
            weather_data.location.name = target_name
            if intent_obj.location:
                intent_obj.location.name = target_name
            else:
                intent_obj.location = LocationTarget(name=target_name, latitude=target_lat, longitude=target_lon)

            analysis = weather_analyzer.analyze(weather_data, intent_obj)
            logger.info(f"[BACKEND WEATHER ANALYSIS] horizon: {analysis.horizon_days}d, variable: {analysis.weather_variable}, focus: {analysis.question_focus}")

        # Check for sector advisory question
        is_advisory = (
            intent_obj.intent in [
                IntentType.AGRICULTURE_ADVISORY,
                IntentType.TRAVEL_ADVISORY,
                IntentType.MARINE_ADVISORY,
                IntentType.AVIATION_ADVISORY
            ]
            or intent_obj.question_focus in [
                "irrigation", "spraying", "agriculture_multi_day", "agriculture_general"
            ]
        )

        advisory_items_payload: List[AdvisoryItem] = []
        advisory_context_dict = None

        if is_advisory:
            target_sector = "agriculture"
            if intent_obj.intent == IntentType.TRAVEL_ADVISORY:
                target_sector = "citizen"
            elif intent_obj.intent == IntentType.MARINE_ADVISORY:
                target_sector = "marine"
            elif intent_obj.intent == IntentType.AVIATION_ADVISORY:
                target_sector = "aviation"

            horizon = intent_obj.time_range.horizon_days if intent_obj.time_range else 1
            sec_resp = advisory_engine.generate_advisory(
                sector=target_sector,
                weather=weather_data,
                alerts=alerts_list,
                context={"crop": intent_obj.crop or "paddy", "horizon_days": horizon}
            )

            # Build advisory items payload
            for adv in sec_resp.advisories:
                advisory_items_payload.append(
                    AdvisoryItem(
                        sector=adv.sector,
                        recommendation=adv.recommendation,
                        action_type="delay" if "DELAY" in adv.recommendation or "POSTPONE" in adv.recommendation else "caution" if "CAUTION" in adv.recommendation or "MONITOR" in adv.recommendation else "proceed",
                        details=adv.basis[0] if adv.basis else ""
                    )
                )

            target_adv = sec_resp.advisories[0]
            if intent_obj.question_focus == "spraying":
                spray_candidates = [a for a in sec_resp.advisories if "Spray" in a.title or "Chemical" in a.title]
                if spray_candidates:
                    target_adv = spray_candidates[0]
            elif intent_obj.question_focus == "irrigation":
                irr_candidates = [a for a in sec_resp.advisories if "Irrigation" in a.title]
                if irr_candidates:
                    target_adv = irr_candidates[0]

            if intent_obj.question_focus == "agriculture_multi_day" and target_adv.horizon_breakdown:
                crop_title = target_adv.crop.title() if target_adv.crop else "Crops"
                lines = [f"🌾 **4-Day Agriculture Advisory for {crop_title} in {target_name}**\n"]
                for b in target_adv.horizon_breakdown:
                    lines.append(f"• **{b['day']}:** Irrigation: `{b['irrigation_verdict']}` | Spraying: `{b['spraying_verdict']}` ({b['condition']}, Rain: {b['rain_probability_pct']}%)")
                lines.append(f"\n👉 **Basis:** {target_adv.basis[0]}")
                lines.append(f"👉 **Source:** {', '.join(target_adv.sources)}")
                deterministic_answer = "\n".join(lines)
            else:
                lines = [
                    f"{target_adv.icon} **{target_adv.title}**",
                    f"\n**Recommendation:** `{target_adv.recommendation.replace('_', ' ')}` (Risk: **{target_adv.risk_level}**)",
                    f"\n{target_adv.basis[0] if target_adv.basis else ''}"
                ]
                if len(target_adv.basis) > 1:
                    lines.append("\n**Why:**")
                    for b in target_adv.basis[1:]:
                        lines.append(f"• {b}")
                if target_adv.recommended_actions:
                    lines.append("\n**Recommended Action:**")
                    for a in target_adv.recommended_actions:
                        lines.append(f"• {a}")
                lines.append(f"\n**Valid until:** {target_adv.valid_until}")
                lines.append(f"**Source:** {', '.join(target_adv.sources)}")
                deterministic_answer = "\n".join(lines)

            final_answer = deterministic_answer
            advisory_context_dict = sec_resp.model_dump()
        else:
            # Deterministic grounded fallback answer (Answers the exact user question)
            deterministic_answer = weather_analyzer.generate_deterministic_answer(analysis, req.message)
            final_answer = deterministic_answer

        # 6. Generative LLM Communication & Explanation (Google Gemini)
        if not isinstance(self.llm_provider, GroundedRuleLLMProvider):
            try:
                alerts_text = "None"
                if alerts_list:
                    alerts_text = "\n".join([f"- {a.severity.value.upper()}: {a.headline}. {a.instruction}" for a in alerts_list])

                if is_advisory and advisory_context_dict:
                    system_prompt = f"""You are the explanation layer of WeatherGPT's Sector Decision Support system.
The backend has already analyzed the actual weather forecast and generated the authoritative advisory.
You must NOT create your own weather prediction.
You must NOT modify the backend recommendation.
You must NOT invent weather values, warnings, authorities, risk levels, or safety information.
Use only the supplied weather data and advisory.
Explain why the recommendation was generated.
If information is missing, explicitly state that it is unavailable.
Do not call a weather condition an official warning unless the supplied data explicitly identifies it as an official warning.
Keep the response concise, structured, direct, and actionable.
Never present unsupported certainty.
Respond in the requested language (Language code: {lang})."""

                    user_prompt = f"""User Question: {req.message}

BACKEND SECTOR ADVISORY DECISION:
{json.dumps(advisory_context_dict, indent=2)}

Active Alerts: {alerts_text}"""
                else:
                    analysis_dict = analysis.model_dump()
                    analysis_json = json.dumps(analysis_dict, indent=2)

                    system_prompt = f"""You are the Weather Intelligence Agent for WeatherGPT.

Your primary responsibility is to understand the user's actual question, regardless of how it is phrased.

CORE OPERATIONAL RULES:
1. Grounded Source of Truth: The supplied Open-Meteo backend data is the ONLY source of truth for factual weather information. Never invent, guess, or fabricate weather observations, forecasts, locations, precipitation probabilities, or warnings.
2. Direct Answer First: Always answer the user's actual question directly in the very first sentence.
3. Multi-Location & Comparisons:
   - When multiple locations are mentioned, compared, or in a route ("from X to Y", "which is warmer: A or B", "compare C and D"), evaluate ALL relevant locations. NEVER answer using only one location.
   - For "best", "worst", "highest", "lowest", "avoid", "compare", "where", "which", provide the direct comparison and ranking clearly before details.
4. Recommendations & Decisions: When the user asks for a recommendation (umbrella, outdoor events, sports, driving, farming), formulate the decision using the available weather evidence rather than simply dumping raw values.
5. Meteorological Explanations ("Why"): When asked "why", explain the physical meteorological drivers based on the data (such as relative humidity, cloud cover, atmospheric pressure, and wind dynamics).
6. Missing Information: If information required to answer is not available in the supplied data, explicitly identify the missing information rather than inventing it.
7. Official Warnings: Distinguish observed conditions and model forecasts from official warnings. Only cite official warnings if they are explicitly present in 'Active Alerts'.
8. Relevance: Do not dump unnecessary weather variables that do not help answer the user's question.
9. Tone: Keep the final response natural, conversational, concise, structured, and helpful.
10. Language: Respond in the requested language (Language code: {lang})."""

                    user_prompt = f"""User Question: {req.message}

BACKEND WEATHER ANALYSIS (Verified Data from Open-Meteo):
{analysis_json}

Active Alerts: {alerts_text}"""

                ai_generated = await self.llm_provider.generate_response(system_prompt, user_prompt)
                if ai_generated and len(ai_generated.strip()) > 10:
                    final_answer = ai_generated.strip()
            except Exception as e:
                logger.warning(f"Gemini synthesis failed ({e}); safely falling back to grounded rule answer.")
                final_answer = deterministic_answer

        # 7. Build UI Summary Payload
        curr = weather_data.current
        target_day = weather_data.daily[0] if weather_data.daily else None
        if intent_obj.time_range and intent_obj.time_range.day_offset == 1 and len(weather_data.daily) > 1:
            target_day = weather_data.daily[1]

        summary = WeatherSummary(
            temperature_c=target_day.temperature_max_c if target_day else curr.temperature_c,
            feels_like_c=curr.feels_like_c,
            condition=target_day.weather_condition if target_day else curr.weather_condition,
            icon=target_day.weather_icon if target_day else curr.weather_icon,
            rainfall_mm=target_day.precipitation_sum_mm if target_day else curr.precipitation_mm,
            rain_probability_pct=target_day.precipitation_probability_max_pct if target_day else (curr.precipitation_probability_pct or 0),
            wind_kmh=target_day.wind_speed_max_kmh if target_day else curr.wind_speed_kmh,
            humidity_pct=curr.relative_humidity_pct
        )

        sources = ["Open-Meteo forecast"]
        if alerts_list:
            sources.append(alerts_list[0].source)

        overall_chat_risk = RiskLevel.LOW
        if alerts_list:
            overall_chat_risk = RiskLevel.MEDIUM
        for adv_item in advisory_items_payload:
            if adv_item.action_type in ["alert", "danger"]:
                overall_chat_risk = RiskLevel.CRITICAL
                break
            elif adv_item.action_type in ["delay", "caution"]:
                overall_chat_risk = RiskLevel.MEDIUM

        return ChatResponse(
            conversation_id=conv_id,
            message_id=msg_id,
            answer=final_answer,
            location=target_name,
            time_range=intent_obj.time_range.relative_day.replace("_", " ").title() if intent_obj.time_range else "Today",
            weather_summary=summary,
            risk_level=overall_chat_risk,
            advisories=advisory_items_payload,
            warnings=alerts_list,
            sources=sources,
            updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            confidence="Based on current forecast data",
            trust_metadata=weather_data.trust,
            tools_called=tools_called,
            language=lang
        )


orchestrator = WeatherIntelligenceOrchestrator()
