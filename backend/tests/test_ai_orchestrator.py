import pytest
from app.ai.intent_parser import intent_parser
from app.ai.orchestrator import orchestrator
from app.schemas.intent import IntentType, UserRole
from app.schemas.chat import ChatRequest


def test_intent_parsing_scenarios():
    # Scenario 1: Rain in Hyderabad tomorrow
    p1 = intent_parser.parse("Will it rain tomorrow in Hyderabad?")
    assert p1.intent in [IntentType.RAINFALL, IntentType.FORECAST]
    assert p1.location.name == "Hyderabad"
    assert p1.time_range.relative_day == "tomorrow"

    # Scenario 2: Farmer Paddy Irrigation
    p2 = intent_parser.parse("Should I irrigate my paddy field tomorrow?")
    assert p2.intent == IntentType.AGRICULTURE_ADVISORY
    assert p2.user_type == UserRole.FARMER
    assert p2.crop == "paddy"

    # Scenario 3: Telugu query
    p3 = intent_parser.parse("రేపు హైదరాబాద్ లో వర్షం పడుతుందా?")
    assert p3.language == "te"
    assert p3.time_range.relative_day == "tomorrow"

    # Scenario 4: Warning query
    p4 = intent_parser.parse("Is there any severe weather warning near me?")
    assert p4.intent == IntentType.WARNING


@pytest.mark.asyncio
async def test_grounded_response_generation():
    req = ChatRequest(
        message="Should I irrigate my field tomorrow?",
        latitude=17.3850,
        longitude=78.4867,
        location_name="Hyderabad",
        user_role="farmer"
    )
    resp = await orchestrator.process_query(req)
    assert resp.location == "Hyderabad"
    assert resp.weather_summary.temperature_c is not None
    assert len(resp.sources) > 0
    assert len(resp.tools_called) > 0
    assert resp.confidence in ["High", "Medium", "Low", "Based on current forecast data", "Forecast confidence: Based on current forecast data"]
