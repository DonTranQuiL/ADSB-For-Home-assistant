import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion.const import DOMAIN, MODE_ZONE
from custom_components.skyradar_fusion.coordinator import (
    SkyRadarFusionCoordinator,
    haversine_distance,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_api():
    with patch(
        "custom_components.skyradar_fusion.coordinator.SkyRadarFusionAPI"
    ) as mock_cls:
        mock_inst = MagicMock()
        mock_inst.get_aircraft_in_zone = AsyncMock(return_value=[])
        mock_inst.get_aircraft_by_callsign = AsyncMock(return_value=[])
        mock_inst.get_aircraft_by_hex = AsyncMock(return_value=[])
        mock_inst.get_planespotters_photo = AsyncMock(return_value=None)
        mock_inst.get_global_emergencies = AsyncMock(return_value=[])
        mock_inst.get_global_military = AsyncMock(return_value=[])
        mock_cls.return_value = mock_inst
        yield mock_inst


def test_haversine_distance_calculation():
    assert haversine_distance(52.0, 5.0, 52.0, 5.0) == 0.0


@pytest.mark.asyncio
async def test_coordinator_zone_analytics(hass: HomeAssistant, mock_api):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "tracking_mode": MODE_ZONE,
            "latitude": 52.0,
            "longitude": 5.0,
            "radius": 10000,
        },
        options={"tracked_list": ["TARGET1"]},
    )
    coord = SkyRadarFusionCoordinator(hass, entry)
    coord.config_entry = (
        entry  # FIX: Prevent DataUpdateCoordinator from setting this to None
    )

    mock_api.get_aircraft_in_zone.return_value = [
        {
            "hex": "A1B2C3",
            "lat": 52.001,
            "lon": 5.001,
            "desc": "Military Drone",
            "flight": "MIL1",
        },
        {
            "hex": "D4E5F6",
            "lat": 59.000,
            "lon": 9.000,
            "desc": "Boeing",
            "flight": "FAR_AWAY",
        },
    ]

    result = await coord._async_update_data()
    assert result["total"] == 1
    assert result["counts"]["military"] == 1
    assert result["closest"]["hex"] == "A1B2C3"


@pytest.mark.asyncio
async def test_coordinator_api_fallbacks(hass: HomeAssistant, mock_api):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"tracking_mode": MODE_ZONE},
        options={"tracked_list": ["EXTERNAL_HEX"]},
    )
    coord = SkyRadarFusionCoordinator(hass, entry)
    coord.config_entry = entry  # FIX
    coord.mode = MODE_ZONE
    coord.tracked_list = ["EXTERNAL_HEX"]

    mock_api.get_aircraft_in_zone.return_value = []
    mock_api.get_aircraft_by_callsign.return_value = []
    mock_api.get_aircraft_by_hex.return_value = [
        {"hex": "EXTERNAL_HEX", "flight": "EXT1", "desc": "Private Jet"}
    ]

    result = await coord._async_update_data()
    assert len(result["tracked_aircraft"]) == 1
    assert result["tracked_aircraft"][0]["flight"] == "EXT1"


@pytest.mark.asyncio
async def test_coordinator_unhandled_exception(hass: HomeAssistant, mock_api):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    coord = SkyRadarFusionCoordinator(hass, entry)
    coord.config_entry = entry  # FIX

    mock_api.get_aircraft_in_zone.side_effect = Exception("API Server Outage")

    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
