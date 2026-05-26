import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion.const import DOMAIN, PLATFORMS


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_coordinator_init():
    with patch(
        "custom_components.skyradar_fusion.SkyRadarFusionCoordinator"
    ) as mock_cls:
        mock_coord = MagicMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.async_request_refresh = AsyncMock()
        mock_cls.return_value = mock_coord
        yield mock_coord


@pytest.mark.asyncio
async def test_setup_unload_and_reload_lifecycle(
    hass: HomeAssistant, mock_coordinator_init
):
    # Mock hass.http to bypass the StaticPathConfig registration
    hass.http = AsyncMock()

    entry = MockConfigEntry(domain=DOMAIN, data={"tracking_mode": "zone_radius"})
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ) as mock_forward:
        assert await hass.config_entries.async_setup(entry.entry_id) is True
        mock_coordinator_init.async_config_entry_first_refresh.assert_called_once()
        assert DOMAIN in hass.data
        mock_forward.assert_called_once_with(entry, PLATFORMS)

    assert hass.services.has_service(DOMAIN, "refresh")
    await hass.services.async_call(DOMAIN, "refresh", blocking=True)
    mock_coordinator_init.async_request_refresh.assert_called_once()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload"
    ) as mock_reload:
        await hass.config_entries.async_reload(entry.entry_id)
        mock_reload.assert_called_once_with(entry.entry_id)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload:
        assert await hass.config_entries.async_unload(entry.entry_id) is True
        mock_unload.assert_called_once_with(entry, PLATFORMS)
