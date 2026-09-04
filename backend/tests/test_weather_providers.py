import pytest
from app.weather.mock import MockProvider
from app.weather.open_meteo import parse_wmo
from app.schemas.weather import UnifiedWeatherResponse


@pytest.mark.asyncio
async def test_mock_provider_returns_demo_data():
    prov = MockProvider()
    assert prov.is_demo is True
    assert "Demo" in prov.provider_name

    res = await prov.get_forecast(17.3850, 78.4867, days=7)
    assert isinstance(res, UnifiedWeatherResponse)
    assert res.trust.is_demo_data is True
    assert len(res.daily) == 7
    assert len(res.hourly) == 24
    assert res.current.temperature_c > 0


def test_wmo_code_mapping():
    cond, icon = parse_wmo(0)
    assert cond == "Clear sky"
    assert icon == "☀️"

    cond_rain, icon_rain = parse_wmo(63)
    assert "rain" in cond_rain.lower()
    assert icon_rain == "🌧️"

    cond_storm, icon_storm = parse_wmo(95)
    assert "thunderstorm" in cond_storm.lower()
