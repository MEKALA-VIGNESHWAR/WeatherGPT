import pytest
from app.advisory.advisory_engine import advisory_engine
from app.weather.mock import MockProvider


@pytest.mark.asyncio
async def test_agriculture_advisory_logic():
    prov = MockProvider()
    weather = await prov.get_forecast(17.3850, 78.4867, days=7)
    alerts = await prov.get_alerts(17.3850, 78.4867)

    adv = advisory_engine.generate_advisory("agriculture", weather, alerts, {"crop": "paddy"})
    assert adv.sector == "agriculture"
    assert len(adv.recommendations) >= 2

    titles = [r.title for r in adv.recommendations]
    assert any("Irrigation" in t for t in titles)
    assert any("Pesticide" in t for t in titles)
