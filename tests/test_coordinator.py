import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.airplanes_live.coordinator import AirplanesLiveCoordinator
from custom_components.airplanes_live.const import DOMAIN, MODE_ZONE

@pytest.fixture
def mock_api():
    api = MagicMock()
    api.get_aircraft_in_zone = AsyncMock(return_value=[])
    api.get_aircraft_by_callsign = AsyncMock(return_value=[])
    api.get_aircraft_by_hex = AsyncMock(return_value=[])
    api.get_planespotters_photo = AsyncMock(return_value=None)
    api.get_global_emergencies = AsyncMock(return_value=[])
    api.get_global_military = AsyncMock(return_value=[])
    return api

@pytest.mark.asyncio
async def test_coordinator_zone_analytics(hass: HomeAssistant, mock_api):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"tracking_mode": MODE_ZONE, "latitude": 52.0, "longitude": 5.0, "radius": 10000},
        options={}
    )
    coord = AirplanesLiveCoordinator(hass, entry)
    coord.api = mock_api
    coord.tracked_list = {"TARGET1"}

    mock_api.get_aircraft_in_zone.return_value = [
        {"hex": "A1B2C3", "lat": 52.001, "lon": 5.001, "desc": "Military Drone", "flight": "MIL1"}
    ]
    
    result = await coord._async_update_data()
    assert result["total"] == 1
    assert result["counts"]["military"] == 1

@pytest.mark.asyncio
async def test_coordinator_api_fallbacks(hass: HomeAssistant, mock_api):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"tracking_mode": MODE_ZONE, "latitude": 52.0, "longitude": 5.0, "radius": 10000},
        options={}
    )
    coord = AirplanesLiveCoordinator(hass, entry)
    coord.api = mock_api
    coord.tracked_list = {"EXTERNAL_HEX"}

    mock_api.get_aircraft_by_hex.return_value = [{"hex": "EXTERNAL_HEX", "flight": "EXT1", "desc": "Private Jet"}]
    result = await coord._async_update_data()
    assert len(result["tracked_aircraft"]) == 1

@pytest.mark.asyncio
async def test_coordinator_unhandled_exception(hass: HomeAssistant, mock_api):
    entry = MockConfigEntry(domain=DOMAIN, data={"tracking_mode": MODE_ZONE}, options={})
    coord = AirplanesLiveCoordinator(hass, entry)
    coord.api = mock_api
    mock_api.get_aircraft_in_zone.side_effect = Exception("API Down")
    
    try:
        await coord._async_update_data()
    except Exception:
        pass
    assert coord.consecutive_errors == 1
    assert coord.last_update_status == "Failed"
