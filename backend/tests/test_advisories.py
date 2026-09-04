import pytest
from app.advisory.advisory_engine import advisory_engine
from app.advisory.config import get_crop_profile, register_crop_profile, CropRuleConfig
from app.advisory.risk_engine import risk_engine
from app.weather.mock import MockProvider


@pytest.mark.asyncio
async def test_agriculture_advisory_logic():
    prov = MockProvider()
    weather = await prov.get_forecast(17.3850, 78.4867, days=7)
    alerts = await prov.get_alerts(17.3850, 78.4867)

    # 1. Paddy Advisory
    adv = advisory_engine.generate_advisory("agriculture", weather, alerts, {"crop": "paddy"})
    assert adv.sector == "agriculture"
    assert len(adv.advisories) >= 2
    assert adv.overall_risk in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    titles = [r.title for r in adv.advisories]
    assert any("Irrigation" in t for t in titles)
    assert any("Chemical" in t or "Spray" in t for t in titles)

    # Verify explainable fields
    irr = next(r for r in adv.advisories if "Irrigation" in r.title)
    assert irr.recommendation in ["DELAY_IRRIGATION", "IRRIGATE", "MONITOR_SOIL_MOISTURE"]
    assert len(irr.basis) > 0
    assert len(irr.recommended_actions) > 0
    assert "Open-Meteo forecast" in irr.sources
    assert len(irr.limitations) > 0


@pytest.mark.asyncio
async def test_crop_profile_registry_and_aliases():
    # Test aliases
    paddy = get_crop_profile("dhan")
    assert paddy.crop_name == "paddy"

    cotton = get_crop_profile("kapas")
    assert cotton.crop_name == "cotton"

    chilli = get_crop_profile("mirchi")
    assert chilli.crop_name == "chilli"

    # Test dynamic registration
    custom_crop = CropRuleConfig(
        crop_name="groundnut",
        display_name="Groundnut (Peanut)",
        aliases=["peanut", "moongfali", "వేరుశనగ"],
        irrigation_rain_prob_delay_pct=40,
        irrigation_rain_mm_delay=2.0,
        water_sensitivity_note="Sensitive to waterlogging during pod filling",
        spray_sensitivity_note="Tikka disease sprays require rain-free foliage"
    )
    register_crop_profile(custom_crop)

    resolved = get_crop_profile("moongfali")
    assert resolved.crop_name == "groundnut"
    assert resolved.irrigation_rain_prob_delay_pct == 40


@pytest.mark.asyncio
async def test_risk_engine_scoring():
    prov = MockProvider()
    weather = await prov.get_forecast(17.3850, 78.4867, days=7)
    score, level, factors = risk_engine.calculate_risk(
        current=weather.current,
        daily=weather.daily[0],
        sector="agriculture"
    )
    assert 0.0 <= score <= 100.0
    assert level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(factors) > 0


@pytest.mark.asyncio
async def test_marine_and_aviation_limitations():
    prov = MockProvider()
    weather = await prov.get_forecast(17.3850, 78.4867, days=7)
    alerts = await prov.get_alerts(17.3850, 78.4867)

    marine_adv = advisory_engine.generate_advisory("marine", weather, alerts)
    assert marine_adv.sector == "marine"
    assert any("wave" in lim.lower() for lim in marine_adv.advisories[0].limitations)

    aviation_adv = advisory_engine.generate_advisory("aviation", weather, alerts)
    assert aviation_adv.sector == "aviation"
    assert any("aviation safety assessment" in lim.lower() for lim in aviation_adv.advisories[0].limitations)


@pytest.mark.asyncio
async def test_multi_day_agriculture_horizon():
    prov = MockProvider()
    weather = await prov.get_forecast(17.3850, 78.4867, days=7)
    alerts = await prov.get_alerts(17.3850, 78.4867)

    adv = advisory_engine.generate_advisory("agriculture", weather, alerts, {"crop": "cotton", "horizon_days": 4})
    assert adv.advisories[0].horizon_breakdown is not None
    assert len(adv.advisories[0].horizon_breakdown) >= 4
