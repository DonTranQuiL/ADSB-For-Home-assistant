import pytest
from unittest.mock import patch
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.airplanes_live.const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_IDENTIFIER_TYPE,
    CONF_IDENTIFIER,
    CONF_TRACKED_LIST,
    CONF_ADD_TRACK,
    CONF_REMOVE_TRACK,
    CONF_CLEAR_TRACK,
    MODE_SINGLE,
    MODE_ZONE,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield


@pytest.mark.asyncio
async def test_config_flow_zone_path(hass):
    """Test user initiating a zone-tracking setup configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Select Zone mode
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TRACKING_MODE: MODE_ZONE}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "zone"

    # Configure zone parameters
    with patch("custom_components.airplanes_live.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={
                CONF_LATITUDE: 52.37,
                CONF_LONGITUDE: 4.89,
                CONF_RADIUS: 10000,
            },
        )
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Zone Tracking"
    assert result3["data"][CONF_TRACKING_MODE] == MODE_ZONE
    assert result3["data"][CONF_RADIUS] == 10000


@pytest.mark.asyncio
async def test_config_flow_single_target_path(hass):
    """Test user initiating a single target aircraft identifier track."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TRACKING_MODE: MODE_SINGLE}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "single"

    with patch("custom_components.airplanes_live.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={
                CONF_IDENTIFIER_TYPE: "callsign",
                CONF_IDENTIFIER: "KLM123",
            },
        )
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Target Tracker"
    assert result3["data"][CONF_IDENTIFIER] == "KLM123"


@pytest.mark.asyncio
async def test_options_flow_modifiers(hass):
    """Test real-time tracking collection modifiers (Add, Remove, Clear)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TRACKING_MODE: MODE_ZONE},
        options={CONF_RADIUS: 5000, CONF_TRACKED_LIST: ["PH-ABC"]},
    )
    entry.add_to_hass(hass)

    # 1. Test Adding a flight
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 6000,
            CONF_ADD_TRACK: "KLM747",
            CONF_REMOVE_TRACK: "",
            CONF_CLEAR_TRACK: False,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert "KLM747" in result2["data"][CONF_TRACKED_LIST]
    assert "PH-ABC" in result2["data"][CONF_TRACKED_LIST]
    assert result2["data"][CONF_RADIUS] == 6000

    # Update entry with new options for next step checks
    hass.config_entries.options.async_update_entry(entry, options=result2["data"])

    # 2. Test Removing a flight
    result_rem = await hass.config_entries.options.async_init(entry.entry_id)
    result_rem2 = await hass.config_entries.options.async_configure(
        result_rem["flow_id"],
        user_input={
            CONF_RADIUS: 6000,
            CONF_ADD_TRACK: "",
            CONF_REMOVE_TRACK: "PH-ABC",
            CONF_CLEAR_TRACK: False,
        },
    )
    assert "PH-ABC" not in result_rem2["data"][CONF_TRACKED_LIST]
    assert "KLM747" in result_rem2["data"][CONF_TRACKED_LIST]

    # 3. Test Clearing the tracked list
    result_clr = await hass.config_entries.options.async_init(entry.entry_id)
    result_clr2 = await hass.config_entries.options.async_configure(
        result_clr["flow_id"],
        user_input={
            CONF_RADIUS: 6000,
            CONF_ADD_TRACK: "",
            CONF_REMOVE_TRACK: "",
            CONF_CLEAR_TRACK: True,
        },
    )
    assert result_clr2["data"][CONF_TRACKED_LIST] == []
