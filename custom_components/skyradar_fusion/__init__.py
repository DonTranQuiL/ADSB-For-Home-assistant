"""The SkyRadar Fusion integration."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import SkyRadarFusionCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ASSETS_URL = "/skyradar_fusion_assets"
CARD_FILE = "skyradar-fusion-card.js"
CARD_VERSION = "2.1.0"
DATA_FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the bundled assets and load the dashboard card (once)."""
    if hass.data.get(DATA_FRONTEND_REGISTERED):
        return
    hass.data[DATA_FRONTEND_REGISTERED] = True
    www = Path(__file__).parent / "www"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(ASSETS_URL, str(www), True)]
        )
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, f"{ASSETS_URL}/{CARD_FILE}?v={CARD_VERSION}")
    except Exception as err:
        _LOGGER.warning("Could not register the SkyRadar Fusion card: %s", err)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration: frontend assets and services, once."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_frontend(hass)

    async def handle_refresh(call: ServiceCall) -> None:
        """Force a data refresh on every loaded entry."""
        for coordinator in list(hass.data.get(DOMAIN, {}).values()):
            if hasattr(coordinator, "async_request_refresh"):
                await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SkyRadar Fusion from a config entry."""
    coordinator = SkyRadarFusionCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    def pre_load_platforms():
        for platform in PLATFORMS:
            importlib.import_module(f".{platform}", __package__)

    await hass.async_add_executor_job(pre_load_platforms)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
