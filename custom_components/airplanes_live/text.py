"""Text entities for Airplanes.Live (FR24 Style)."""
from homeassistant.components.text import TextEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        AirplanesLiveAddText(coordinator),
        AirplanesLiveRemoveText(coordinator)
    ])

class AirplanesLiveTextBase(TextEntity):
    has_entity_name = True
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Airplanes.Live Tracker"
        )
        self._attr_native_value = ""

class AirplanesLiveAddText(AirplanesLiveTextBase):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Add to track"
        self._attr_icon = "mdi:airplane-plus"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_add_track"

    async def async_set_value(self, value: str) -> None:
        clean_val = value.strip().upper().replace(" ", "")
        if clean_val:
            self.coordinator.add_track(clean_val)
            self._attr_native_value = ""
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

class AirplanesLiveRemoveText(AirplanesLiveTextBase):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Remove from track"
        self._attr_icon = "mdi:airplane-minus"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_remove_track"

    async def async_set_value(self, value: str) -> None:
        clean_val = value.strip().upper().replace(" ", "")
        if not clean_val: 
            return
        
        # BULLETPROOF GHOST CLEANUP VOOR STANDALONE TRACKERS
        registry = er.async_get(self.hass)
        entries = er.async_entries_for_config_entry(registry, self.coordinator.config_entry.entry_id)
        for entry in entries:
            if entry.domain == "device_tracker":
                # Kijkt nu in het entiteit-ID zelf (device_tracker.airplanes_live_klm123)
                if clean_val in entry.entity_id.upper() or clean_val in (entry.original_name or "").upper():
                    registry.async_remove(entry.entity_id)

        self.coordinator.remove_track(clean_val)
        self._attr_native_value = ""
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
