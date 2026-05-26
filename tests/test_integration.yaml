import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion.const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    MODE_ZONE,
)


# =========================================================================
# 1. CONFIG FLOW TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_config_flow_zone_setup(hass: HomeAssistant):
    """Test setting up the integration in Zone Tracking mode."""
    # Step 1: User selects Zone Mode
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRACKING_MODE: MODE_ZONE},
    )
    assert result2["step_id"] == "zone"

    # Step 2: User inputs coordinates and radius
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_LATITUDE: 52.0,
            CONF_LONGITUDE: 5.0,
            CONF_RADIUS: 10000,
        },
    )
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Zone Tracking"
    assert result3["data"][CONF_RADIUS] == 10000


# =========================================================================
# 2. COORDINATOR & SENSOR TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_sensors_and_coordinator_data(hass: HomeAssistant):
    """Test that the coordinator processes API data and sensors update correctly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SkyRadar Fusio",
        data={
            CONF_TRACKING_MODE: MODE_ZONE,
            # Center point coordinates
            CONF_LATITUDE: 52.0,
            CONF_LONGITUDE: 5.0,
            CONF_RADIUS: 5000,
        },
        entry_id="airplanes_test_id",
    )
    entry.add_to_hass(hass)

    # Fake aircraft payload returned by the API
    mock_aircraft_data = [
        # Aircraft 1: Close by, should be classified as commercial
        {"hex": "A123", "flight": "KLM456", "lat": 52.01, "lon": 5.01, "desc": "Boeing 737", "alt_baro": 10000},
        # Aircraft 2: Close by, should be classified as helicopter
        {"hex": "B789", "flight": "HELI1", "lat": 52.005, "lon": 5.005, "desc": "rotorcraft", "alt_baro": 1500},
        # Aircraft 3: Too far away (outside 5000m radius), should be ignored
        {"hex": "C000", "flight": "FARAWAY", "lat": 53.0, "lon": 6.0, "desc": "military", "alt_baro": 30000},
    ]

    mock_api = MagicMock()
    mock_api.get_aircraft_in_zone = AsyncMock(return_value=mock_aircraft_data)

    with patch(
        "custom_components.skyradar_fusion.coordinator.AirplanesLiveAPI",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # 1. Check Overview Sensor (Should be 2 total, because 1 is out of range)
        overview_sensor = hass.states.get(f"sensor.skyradar_fusion_tracker_current_in_area")
        assert overview_sensor is not None
        assert overview_sensor.state == "2"
        
        # Check attributes to ensure closest flight logic works
        attrs = overview_sensor.attributes
        assert "Closest Flight" in attrs
        assert attrs["Closest Flight"] in ["KLM456", "HELI1"]

        # 2. Check Category Sensors
        commercial_sensor = hass.states.get(f"sensor.skyradar_fusion_tracker_commercials_in_area")
        assert commercial_sensor is not None
        assert commercial_sensor.state == "1"

        heli_sensor = hass.states.get(f"sensor.skyradar_fusion_tracker_helicopters_in_area")
        assert heli_sensor is not None
        assert heli_sensor.state == "1"

        military_sensor = hass.states.get(f"sensor.skyradar_fusion_tracker_militarys_in_area")
        assert military_sensor is not None
        assert military_sensor.state == "0"
