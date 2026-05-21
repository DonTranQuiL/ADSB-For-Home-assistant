"""Test the Airplanes.Live Tracker config flow."""
from unittest.mock import patch
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from custom_components.airplanes_live.const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_IDENTIFIER_TYPE,
    CONF_IDENTIFIER,
    CONF_GLOBAL_EMERGENCY,
    CONF_GLOBAL_MILITARY,
    CONF_ENABLE_TRACKER,
    MODE_ZONE,
    MODE_SINGLE,
)

async def test_form_zone(hass: HomeAssistant) -> None:
    """Test we get the form for zone tracking and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRACKING_MODE: MODE_ZONE},
    )
    assert result2["type"] == "form"
    assert result2["step_id"] == "zone"

    with patch(
        "custom_components.airplanes_live.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_LATITUDE: 50.83,
                CONF_LONGITUDE: 6.1,
                CONF_RADIUS: 5000,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] == "create_entry"
    assert result3["title"] == "Zone Tracking"
    assert result3["data"] == {
        CONF_TRACKING_MODE: MODE_ZONE,
        CONF_LATITUDE: 50.83,
        CONF_LONGITUDE: 6.1,
        CONF_RADIUS: 5000,
    }
    assert len(mock_setup_entry.mock_calls) == 1

async def test_form_single(hass: HomeAssistant) -> None:
    """Test we get the form for single target tracking and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRACKING_MODE: MODE_SINGLE},
    )
    assert result2["type"] == "form"
    assert result2["step_id"] == "single"

    with patch(
        "custom_components.airplanes_live.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_IDENTIFIER_TYPE: "callsign",
                CONF_IDENTIFIER: "KLM123",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] == "create_entry"
    assert result3["title"] == "Target Tracker"
    assert result3["data"] == {
        CONF_TRACKING_MODE: MODE_SINGLE,
        CONF_IDENTIFIER_TYPE: "callsign",
        CONF_IDENTIFIER: "KLM123",
    }
    assert len(mock_setup_entry.mock_calls) == 1

async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    config_entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Airplanes.Live",
        data={
            CONF_TRACKING_MODE: MODE_ZONE,
            CONF_LATITUDE: 50.83,
            CONF_LONGITUDE: 6.1,
            CONF_RADIUS: 5000,
        },
        source=config_entries.SOURCE_USER,
        options={},
        discovery_keys=None,
        unique_id=None,
    )
    
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 10000,
            CONF_ENABLE_TRACKER: False,
            CONF_GLOBAL_EMERGENCY: True,
            CONF_GLOBAL_MILITARY: False,
        },
    )

    assert result2["type"] == "create_entry"
    assert config_entry.options == {
        CONF_RADIUS: 10000,
        CONF_ENABLE_TRACKER: False,
        CONF_GLOBAL_EMERGENCY: True,
        CONF_GLOBAL_MILITARY: False,
    }
