import pytest
import asyncio
from app.ai.intent_parser import intent_parser
from app.ai.orchestrator import orchestrator
from app.alerts.alert_service import warning_service
from app.schemas.chat import ChatRequest
from app.schemas.intent import IntentType


@pytest.mark.asyncio
async def test_multi_location_temperature_comparison():
    # Query: "Is Mumbai warmer than Delhi?"
    req = ChatRequest(message="Is Mumbai warmer than Delhi?")
    resp = await orchestrator.process_query(req)
    
    assert "Mumbai" in resp.location
    assert "Delhi" in resp.location
    # Answer must address the comparison
    assert any(term in resp.answer.lower() for term in ["warmer", "cooler", "temperature", "similar", "mumbai", "delhi"])
    # Tool traces must reflect both locations
    assert len(resp.tools_called) >= 2


@pytest.mark.asyncio
async def test_multi_location_rain_avoidance():
    # Query: "Which has less rain: Pune or Goa?"
    req = ChatRequest(message="Which has less rain: Pune or Goa?")
    resp = await orchestrator.process_query(req)
    
    assert "Pune" in resp.location
    assert "Goa" in resp.location
    assert any(term in resp.answer.lower() for term in ["rain", "chance", "dry", "lowest", "pune", "goa"])
    assert len(resp.tools_called) >= 2


@pytest.mark.asyncio
async def test_route_weather():
    # Query: "Weather driving from Chennai to Bangalore"
    req = ChatRequest(message="Weather driving from Chennai to Bangalore")
    resp = await orchestrator.process_query(req)
    
    assert "Chennai" in resp.location
    assert ("Bangalore" in resp.location or "Bengaluru" in resp.location)
    assert any(term in resp.answer.lower() for term in ["route", "origin", "destination", "chennai", "bangalore", "bengaluru", "driving", "travel"])
    assert len(resp.tools_called) >= 2


@pytest.mark.asyncio
async def test_why_meteorological_explanation():
    # Query: "Why is it raining in Mumbai?"
    req = ChatRequest(message="Why is it raining in Mumbai?")
    resp = await orchestrator.process_query(req)
    
    assert "Mumbai" in resp.location
    # Answer must contain physical meteorological factors
    assert any(term in resp.answer.lower() for term in ["humidity", "cloud", "moisture", "pressure", "atmosphere", "meteorological", "rain"])


def test_sample_cyclone_bulletin_loaded():
    # Visakhapatnam is near lat 17.6868, lon 83.2185
    alerts_resp = warning_service.get_alerts_for_location(17.6868, 83.2185, location_name="Visakhapatnam")
    
    # Must find the active official IMD cyclone bulletin
    assert alerts_resp.count >= 1
    cyclone_alerts = [a for a in alerts_resp.alerts if "Cyclonic Storm" in a.headline or "BOB/03/2026" in a.headline]
    assert len(cyclone_alerts) >= 1
    alert = cyclone_alerts[0]
    assert alert.source == "Cyclone Warning Division, IMD New Delhi"
    assert "Visakhapatnam" in alert.instruction or "Bay of Bengal" in alert.area_desc
