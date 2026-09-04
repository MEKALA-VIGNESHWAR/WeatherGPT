import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.ai.intent_parser import intent_parser
from app.ai.tools import weather_tools
from app.ai.llm_provider import get_llm_provider
from app.ai.translations import get_translated_string
from app.ai.rag_service import rag_service
from app.schemas.chat import (
    ChatRequest, ChatResponse, WeatherSummary, RiskLevel, AdvisoryItem, ToolCallTrace
)
from app.schemas.intent import IntentType, UserRole
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

        # 1. Query Understanding & Intent Parsing
        intent_obj = intent_parser.parse(
            query=req.message,
            default_lat=req.latitude or 17.3850,
            default_lon=req.longitude or 78.4867,
            default_loc_name=req.location_name or "Hyderabad",
            user_role_hint=req.user_role,
            lang_hint=req.language
        )
        logger.info(f"Parsed intent: {intent_obj.intent.value} for {intent_obj.location.name} in lang {intent_obj.language}")

        target_lat = intent_obj.location.latitude or req.latitude or 17.3850
        target_lon = intent_obj.location.longitude or req.longitude or 78.4867
        target_name = intent_obj.location.name or req.location_name or "Hyderabad"
        lang = intent_obj.language or req.language or "en"
        rel_time = intent_obj.time_range.relative_day if intent_obj.time_range else "today"

        # 2. Tool Execution (Verified Data Retrieval - Zero Fabrication)
        tool_t0 = time.time()
        weather_data = await weather_tools.get_forecast(target_lat, target_lon, days=7)
        tools_called.append(
            ToolCallTrace(
                tool_name="get_forecast",
                arguments={"latitude": target_lat, "longitude": target_lon, "days": 7},
                execution_time_ms=round((time.time() - tool_t0) * 1000, 1)
            )
        )

        tool_t1 = time.time()
        active_alerts_resp = await weather_tools.get_active_alerts(target_lat, target_lon, location_name=target_name)
        tools_called.append(
            ToolCallTrace(
                tool_name="get_active_alerts",
                arguments={"latitude": target_lat, "longitude": target_lon},
                execution_time_ms=round((time.time() - tool_t1) * 1000, 1)
            )
        )

        # Retrieve relevant RAG guidance
        rag_docs = rag_service.search(req.message, top_k=1)

        # 3. Data Extraction for Target Time
        curr = weather_data.current
        daily = weather_data.daily
        is_tomorrow = (rel_time == "tomorrow")
        target_day = daily[1] if (is_tomorrow and len(daily) > 1) else (daily[0] if daily else None)

        temp_c = target_day.temperature_max_c if target_day else curr.temperature_c
        rain_prob = target_day.precipitation_probability_max_pct if target_day else (curr.precipitation_probability_pct or 0)
        rain_sum_mm = target_day.precipitation_sum_mm if target_day else curr.precipitation_mm
        wind_speed = target_day.wind_speed_max_kmh if target_day else curr.wind_speed_kmh
        condition = target_day.weather_condition if target_day else curr.weather_condition
        icon = target_day.weather_icon if target_day else curr.weather_icon

        # 4. Context & Risk Analysis
        risk_level = RiskLevel.LOW
        advisories: List[AdvisoryItem] = []
        alerts_list = active_alerts_resp.alerts

        if any(a.severity == AlertSeverity.RED for a in alerts_list):
            risk_level = RiskLevel.CRITICAL
        elif any(a.severity == AlertSeverity.ORANGE for a in alerts_list):
            risk_level = RiskLevel.HIGH
        elif rain_prob >= 70 or rain_sum_mm >= 25.0 or temp_c >= 41.0 or any(a.severity == AlertSeverity.YELLOW for a in alerts_list):
            risk_level = RiskLevel.MEDIUM

        time_label = "tomorrow" if is_tomorrow else "today"

        # Agriculture context
        if intent_obj.intent == IntentType.AGRICULTURE_ADVISORY or intent_obj.user_type == UserRole.FARMER:
            if "spray" in req.message.lower() or "pesticide" in req.message.lower() or "పురుగుమందు" in req.message:
                if rain_prob >= 40:
                    spray_advice = get_translated_string("spray_delay", lang=lang, rain=rain_sum_mm)
                    advisories.append(AdvisoryItem(sector="agriculture", recommendation=spray_advice, action_type="delay"))
                else:
                    spray_advice = get_translated_string("spray_safe", lang=lang, wind=wind_speed)
                    advisories.append(AdvisoryItem(sector="agriculture", recommendation=spray_advice, action_type="proceed"))
            else:
                # Irrigation
                if rain_prob >= 50 or rain_sum_mm >= 5.0:
                    irrig_advice = get_translated_string("irrigation_delay", lang=lang, rain=rain_sum_mm)
                    advisories.append(AdvisoryItem(sector="agriculture", recommendation=irrig_advice, action_type="delay"))
                else:
                    irrig_advice = get_translated_string("irrigation_safe", lang=lang, prob=rain_prob)
                    advisories.append(AdvisoryItem(sector="agriculture", recommendation=irrig_advice, action_type="proceed"))

        # Travel context
        elif intent_obj.intent == IntentType.TRAVEL_ADVISORY:
            if rain_prob >= 50:
                travel_advice = get_translated_string("travel_caution", lang=lang)
                advisories.append(AdvisoryItem(sector="travel", recommendation=travel_advice, action_type="caution"))

        # 5. Grounded LLM Explanation Formulation
        # Construct grounded response respecting verified facts
        answer_parts = []

        if rain_prob >= 50 or rain_sum_mm >= 2.5:
            rain_statement = get_translated_string("rain_expected", lang=lang, location=target_name, time_desc=time_label)
        else:
            rain_statement = get_translated_string("no_rain", lang=lang, location=target_name, time_desc=time_label)
        answer_parts.append(f"{icon} {rain_statement}")

        # Metrics overview
        temp_statement = get_translated_string("temp_forecast", lang=lang, temp=temp_c, humidity=curr.relative_humidity_pct)
        answer_parts.append(temp_statement)

        # Include specific recommendation if applicable
        for adv in advisories:
            answer_parts.append(adv.recommendation)

        # Prominently include Official Warnings if active
        if alerts_list:
            top_alert = alerts_list[0]
            alert_statement = get_translated_string(
                "warning_alert", lang=lang,
                headline=top_alert.headline,
                instruction=top_alert.instruction
            )
            answer_parts.insert(0, f"⚠️ {alert_statement}")

        final_answer = "\n\n".join(answer_parts)

        # Weather summary payload
        summary = WeatherSummary(
            temperature_c=temp_c,
            feels_like_c=curr.feels_like_c,
            condition=condition,
            icon=icon,
            rainfall_mm=rain_sum_mm,
            rain_probability_pct=rain_prob,
            wind_kmh=wind_speed,
            humidity_pct=curr.relative_humidity_pct
        )

        sources = [weather_data.trust.source]
        if alerts_list:
            sources.append(alerts_list[0].source)
        if rag_docs:
            sources.append(f"{rag_docs[0].source} ({rag_docs[0].authority})")

        return ChatResponse(
            conversation_id=conv_id,
            message_id=msg_id,
            answer=final_answer,
            location=target_name,
            time_range=time_label.title(),
            weather_summary=summary,
            risk_level=risk_level,
            advisories=advisories,
            warnings=alerts_list,
            sources=sources,
            updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            confidence=weather_data.trust.confidence.value.title(),
            trust_metadata=weather_data.trust,
            tools_called=tools_called,
            language=lang
        )


orchestrator = WeatherIntelligenceOrchestrator()
