import pytest
from unittest.mock import MagicMock
from homeassistant.components.device_tracker.const import SourceType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion.const import DOMAIN
from custom_components.skyradar_fusion.device_tracker import (
    SkyRadarFusionTracker,
    async_setup_entry,
)


@pytest.fixture
def mock_tracker_coord():
    coord = MagicMock()
    coord.config_entry = MockConfigEntry(
        domain=DOMAIN, entry_id="tracker_test", options={}
    )
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
                "distance_meter": 500,
            }
        ]
    }
    return coord


@pytest.mark.asyncio
async def test_async_setup_entry_device_tracker(hass, mock_tracker_coord):
    hass.data.setdefault(DOMAIN, {})["tracker_test"] = mock_tracker_coord
    entry = MockConfigEntry(domain=DOMAIN, entry_id="tracker_test")
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called


def test_device_tracker_properties_and_icons(mock_tracker_coord):
    tracker_heli = SkyRadarFusionTracker(mock_tracker_coord, "A4B5C6")

    # Name check updated to match user's device_tracker.py format
    assert tracker_heli.name == "skyradar_fusion_HELI1"
    assert tracker_heli.unique_id == "skyradar_fusion_A4B5C6"
    assert tracker_heli.latitude == 52.1
    assert tracker_heli.longitude == 5.1
    assert tracker_heli.source_type == SourceType.GPS
    assert tracker_heli.icon == "mdi:helicopter"
    assert tracker_heli.entity_picture == "/skyradar_fusion_assets/planes/H135.png"
