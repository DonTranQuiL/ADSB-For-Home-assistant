import pytest
from unittest.mock import patch
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion.const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_IDENTIFIER_TYPE,
    CONF_IDENTIFIER,
    CONF_GLOBAL_EMERGENCY,
    CONF_GLOBAL_MILITARY,
    MODE_SINGLE,
    MODE_ZONE,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield


@pytest.mark.asyncio
async def test_form_zone(hass):
    """Test we get the form for zone tracking and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TRACKING_MODE: MODE_ZONE}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "zone"

    with patch(
        "custom_components.skyradar_fusion.async_setup_entry", return_value=True
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={
                CONF_LATITUDE: 52.0,
                CONF_LONGITUDE: 5.0,
                CONF_RADIUS: 10000,
            },
        )
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["data"][CONF_TRACKING_MODE] == MODE_ZONE


@pytest.mark.asyncio
async def test_form_single(hass):
    """Test we get the form for single target tracking and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TRACKING_MODE: MODE_SINGLE}
    )
    assert result2["step_id"] == "single"

    with patch(
        "custom_components.skyradar_fusion.async_setup_entry", return_value=True
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={
                CONF_IDENTIFIER_TYPE: "callsign",
                CONF_IDENTIFIER: "KLM123",
            },
        )
    assert result3["type"] == FlowResultType.CREATE_ENTRY


@pytest.mark.asyncio
async def test_options_flow(hass):
    """Test config flow options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TRACKING_MODE: MODE_ZONE},
        options={CONF_RADIUS: 5000},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 6000,
            CONF_GLOBAL_EMERGENCY: True,
            CONF_GLOBAL_MILITARY: False,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_RADIUS] == 6000
    assert result2["data"][CONF_GLOBAL_EMERGENCY] is True
