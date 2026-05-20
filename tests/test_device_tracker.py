import pytest
from unittest.mock import MagicMock
from homeassistant.components.device_tracker.const import SourceType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.airplanes_live.const import DOMAIN
from custom_components.airplanes_live.device_tracker import AirplanesLiveTracker, async_setup_entry

@pytest.fixture
def mock_tracker_coord():
    coord = MagicMock()
    coord.config_entry = MockConfigEntry(domain=DOMAIN, entry_id="tracker_test")
    coord.data = {
        "tracked_aircraft": [
            {
                "hex": "A4B5C6",
                "flight": "HELI1",
                "desc": "Rotorcraft",
                "baro_rate": 500,
                "lat": 52.1,
                "lon": 5.1,
                "t": "H135",
                "air_category": "helicopter",
                "alt_baro": 1500,
                "track": 180,
                "r": "PH-XY",
                "distance_meter": 500
            },
            {
                "hex": "GLID99",
                "flight": "",
                "desc": "Glider",
                "baro_rate": -300,
                "lat": 52.2,
                "lon": 5.2,
                "t": None,
                "air_category": "private"
            }
        ]
    }
    return coord


@pytest.mark.asyncio
async def test_async_setup_entry_device_tracker(hass, mock_tracker_coord):
    """Test that device tracker setup appends current targets cleanly."""
    hass.data.setdefault(DOMAIN, {})["tracker_test"] = mock_tracker_coord
    entry = MockConfigEntry(domain=DOMAIN, entry_id="tracker_test")
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)
    # Should call async_add_entities with both tracked aircraft
    assert async_add_entities.called


def test_device_tracker_properties_and_icons(mock_tracker_coord):
    """Test tracking engine updates parameters, dynamic climb icons, and model profiles."""
    tracker_heli = AirplanesLiveTracker(mock_tracker_coord, "A4B5C6")
    tracker_glider = AirplanesLiveTracker(mock_tracker_coord, "GLID99")

    # Name and Unique ID checks
    assert tracker_heli.name == "Tracked Flight HELI1"
    assert tracker_glider.name == "Tracked Flight GLID99" # Empty flight string fallbacks
    assert tracker_heli.unique_id == "airplanes_live_A4B5C6"

    # GPS state verification
    assert tracker_heli.latitude == 52.1
    assert tracker_heli.longitude == 5.1
    assert tracker_heli.source_type == SourceType.GPS

    # Dynamic icon verification branches (climbing vs gliding)
    assert tracker_heli.icon == "mdi:helicopter"
    assert tracker_glider.icon == "mdi:paper-airplane"

    # Picture generation maps
    assert tracker_heli.entity_picture == "/local/airplanes/H135.png"
    assert tracker_glider.entity_picture is None

    # Verify tracking state arrays map completely
    attrs = tracker_heli.extra_state_attributes
    assert attrs["Category"] == "helicopter"
    assert attrs["Registration"] == "PH-XY"
    assert attrs["Altitude"] == 1500
