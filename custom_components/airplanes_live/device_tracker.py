"""Device tracker platform for Airplanes.Live."""
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, CONF_ENABLE_TRACKER

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    tracked_hexes = set()
    
    @callback
    def _update():
        if not coordinator.config_entry.options.get(CONF_ENABLE_TRACKER, True):
            registry = er.async_get(hass)
            entries = er.async_entries_for_config_entry(registry, config_entry.entry_id)
            for entry in entries:
                if entry.domain == "device_tracker":
                    registry.async_remove(entry.entity_id)
            tracked_hexes.clear()
            return

        new = []
        for ac in coordinator.data.get("tracked_aircraft", []):
            if ac.get("hex") not in tracked_hexes:
                tracked_hexes.add(ac.get("hex"))
                new.append(AirplanesLiveTracker(coordinator, ac.get("hex")))
        if new: 
            async_add_entities(new)
        
    coordinator.async_add_listener(_update)
    _update()


class AirplanesLiveTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator, hex_id):
        super().__init__(coordinator)
        self._hex_id = hex_id
        
        ac_data = self._ac()
        callsign = ac_data.get("flight", "").strip() or self._hex_id
        
        # STANDALONE ENTITEIT INSTELLINGEN (Niet tonen in Apparaat/Diagnostics)
        self._attr_has_entity_name = False
        self._attr_name = f"airplanes_live_{callsign}"
        self._attr_unique_id = f"airplanes_live_{self._hex_id}"
        # We stellen BEWUST GEEN self._attr_device_info in!

    def _ac(self):
        return next((ac for ac in self.coordinator.data.get("tracked_aircraft", []) if ac.get("hex") == self._hex_id), {})

    @property
    def latitude(self): return self._ac().get("lat")

    @property
    def longitude(self): return self._ac().get("lon")

    @property
    def source_type(self): return SourceType.GPS

    @property
    def icon(self):
        ac = self._ac()
        ac_type = ac.get("desc", "").lower()
        baro_rate = ac.get("baro_rate", 0)

        if "heli" in ac_type or "rotor" in ac_type: 
            return "mdi:helicopter"
            
        if "glider" in ac_type: 
            return "mdi:paper-airplane"
            
        if "balloon" in ac_type: 
            return "mdi:hot-air-balloon"

        if baro_rate > 250: 
            return "mdi:airplane-takeoff"
            
        elif baro_rate < -250: 
            return "mdi:airplane-landing"
            
        return "mdi:airplane"

    @property
    def entity_picture(self):
        ac_data = self._ac()
        
        api_photo = ac_data.get("api_photo_url")
        if api_photo:
            return api_photo
            
        icao_type = ac_data.get("t")
        if icao_type: 
            return f"/airplanes_live_assets/planes/{icao_type.upper()}.png"
            
        return None

    @property
    def extra_state_attributes(self):
        ac = self._ac()
        return {
            "Category": ac.get("air_category"), 
            "Altitude": ac.get("alt_baro"), 
            "Heading (deg)": ac.get("track"),
            "Registration": ac.get("r", "Unknown"),
            "Type": ac.get("t", "Unknown"),
            "Distance (m)": ac.get("distance_meter", "N/A")
        }
