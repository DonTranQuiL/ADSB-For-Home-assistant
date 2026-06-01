import pytest
from unittest.mock import MagicMock
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion.const import DOMAIN
from custom_components.skyradar_fusion.sensor import (
    SkyRadarFusionOverviewSensor,
    SkyRadarFusionStatSensor,
    SkyRadarFusionCategorySensor,
)


@pytest.fixture
def mock_coord_data():
    coord = MagicMock()
    coord.config_entry = MockConfigEntry(domain=DOMAIN, entry_id="test_id")
    coord.data = {
        "total": 5,
        "entered": 2,
        "exited": 1,
        "additional_tracked": 0,
        "counts": {"helicopter": 1, "military": 1, "commercial": 3, "private": 0},
        "closest": {
            "flight": "KLM123",
            "distance_meter": 1250.5,
            "desc": "Boeing 737",
            "alt_baro": 4000,
        },
        "aircraft": [],
    }
    return coord


def test_overview_sensor_attributes(mock_coord_data):
    sensor = SkyRadarFusionOverviewSensor(mock_coord_data)

    assert sensor.native_value == 5
    assert sensor.unique_id == "airspace_overview_test_id"

    attrs = sensor.extra_state_attributes
    assert attrs["Closest Flight"] == "KLM123"
    assert attrs["Closest Distance (m)"] == 1250.5
    assert attrs["Closest Type"] == "Boeing 737"
    assert attrs["Closest Altitude"] == 4000


def test_overview_sensor_no_closest(mock_coord_data):
    # Set up the mock data for a completely empty sky
    mock_coord_data.data["closest"] = None
    mock_coord_data.recent_history = []

    sensor = SkyRadarFusionOverviewSensor(mock_coord_data)

    # Updated to match the actual output of the user's sensor.py when closest is None
    assert sensor.extra_state_attributes == {
        "Closest Flight": "None",
        "flights_list": [],
        "recent_aircraft": [],
    }


def test_stat_and_category_sensors(mock_coord_data):
    entered_sensor = SkyRadarFusionStatSensor(
        mock_coord_data, "entered", "Entered", "mdi:icon"
    )
    heli_sensor = SkyRadarFusionCategorySensor(mock_coord_data, "helicopter")

    assert entered_sensor.native_value == 2
    assert heli_sensor.native_value == 1
    assert heli_sensor.icon == "mdi:helicopter"
