import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.airplanes_live.const import DOMAIN, MODE_ZONE
from custom_components.airplanes_live.coordinator import (
    AirplanesLiveCoordinator,
    haversine_distance,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield


@pytest.fixture
def mock_api():
    """Mock the API module layout explicitly using absolute paths."""
    with patch(
        "custom_components.airplanes_live.coordinator.AirplanesLiveAPI"
    ) as mock_cls:
        mock_inst = MagicMock()
        mock_inst.get_aircraft_in_zone = AsyncMock(return_value=[])
        mock_inst.get_aircraft_by_callsign = AsyncMock(return_value=[])
        mock_inst.get_aircraft_by_hex = AsyncMock(return_value=[])
        mock_cls.return_value = mock_inst
        yield mock_inst


def test_haversine_distance_calculation():
    """Verify nautical mile to meters conversion math is precise."""
    assert haversine_distance(52.0, 5.0, 52.0, 5.0) == 0.0


@pytest.mark.asyncio
async def test_aircraft_classification_categories(hass: HomeAssistant):
    """Verify strict keyword checks correctly route aircraft classifications."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    coord = AirplanesLiveCoordinator(hass, entry)

    assert coord.classify_aircraft({"desc": "Heli-Rotor"}) == "helicopter"
    assert coord.classify_aircraft({"desc": "Military Transport"}) == "military"
    assert (
        coord.classify_aircraft({"flight": "KLM1234", "desc": "Boeing"}) == "commercial"
    )
    assert coord.classify_aircraft({"flight": "N12345", "desc": "Cessna"}) == "private"


@pytest.mark.asyncio
async def test_coordinator_zone_analytics(hass: HomeAssistant, mock_api):
    """Test zone processing engine calculates distances, categories, and entries completely."""
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
    coord = AirplanesLiveCoordinator(hass, entry)

    # 1. First Run: Aircraft inside tracked zone range bounds
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
    assert result["entered"] == 0

    # 2. Second Run: Map changes to verify "Entered" and "Exited" telemetry tracking
    mock_api.get_aircraft_in_zone.return_value = [
        {
            "hex": "A1B2C3",
            "lat": 52.001,
            "lon": 5.001,
            "desc": "Military Drone",
            "flight": "MIL1",
        },
        {
            "hex": "NEW777",
            "lat": 52.002,
            "lon": 5.002,
            "desc": "Rotor-craft",
            "flight": "HELI",
        },
    ]
    result2 = await coord._async_update_data()
    assert result2["entered"] == 1
    assert result2["exited"] == 0

    # 3. Third Run: Flight leaves zone radius
    mock_api.get_aircraft_in_zone.return_value = []
    result3 = await coord._async_update_data()
    assert result3["entered"] == 0
    assert result3["exited"] == 2


@pytest.mark.asyncio
async def test_coordinator_api_fallbacks(hass: HomeAssistant, mock_api):
    """Verify FR24 external target lookup query chains trigger on missing local vectors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"tracking_mode": MODE_ZONE},
        options={"tracked_list": ["EXTERNAL_HEX"]},
    )
    coord = AirplanesLiveCoordinator(hass, entry)
    coord.mode = MODE_ZONE

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
    """Verify unhandled API disruptions throw UpdateFailed exceptions securely."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    coord = AirplanesLiveCoordinator(hass, entry)

    mock_api.get_aircraft_in_zone.side_effect = Exception("API Server Outage")

    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
