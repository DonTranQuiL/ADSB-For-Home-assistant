import pytest
from unittest.mock import MagicMock
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.airplanes_live.const import DOMAIN
from custom_components.airplanes_live.sensor import (
    AirplanesLiveOverviewSensor,
    AirplanesLiveStatSensor,
    AirplanesLiveCategorySensor,
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
    }
    return coord


def test_overview_sensor_attributes(mock_coord_data):
    """Verify airspace overview telemetry maps target data states cleanly."""
    sensor = AirplanesLiveOverviewSensor(mock_coord_data)

    assert sensor.native_value == 5
    assert sensor.unique_id == "airspace_overview_test_id"

    attrs = sensor.extra_state_attributes
    assert attrs["Closest Flight"] == "KLM123"
    assert attrs["Closest Distance (m)"] == 1250.5
    assert attrs["Closest Type"] == "Boeing 737"
    assert attrs["Closest Altitude"] == 4000


def test_overview_sensor_no_closest(mock_coord_data):
    """Verify overview attributes fall back cleanly when no aircraft are visible."""
    mock_coord_data.data["closest"] = None
    sensor = AirplanesLiveOverviewSensor(mock_coord_data)
    assert sensor.extra_state_attributes == {"Closest": "None"}


def test_stat_and_category_sensors(mock_coord_data):
    """Verify category splitting and entity isolation categories match completely."""
    entered_sensor = AirplanesLiveStatSensor(
        mock_coord_data, "entered", "Entered", "mdi:icon"
    )
    heli_sensor = AirplanesLiveCategorySensor(mock_coord_data, "helicopter")

    assert entered_sensor.native_value == 2
    assert heli_sensor.native_value == 1
    assert heli_sensor.icon == "mdi:helicopter"
