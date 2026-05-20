"""Device tracker platform for Airplanes.Live."""
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    tracked_hexes = set()
    
    @callback
    def _update():
        new = []
        # OPMERKING: We itereren hier ALLEEN over de specifiek getrackte vliegtuigen!
        for ac in coordinator.data.get("tracked_aircraft", []):
            if ac.get("hex") not in tracked_hexes:
                tracked_hexes.add(ac.get("hex"))
                new.append(AirplanesLiveTracker(coordinator, ac.get("hex")))
        if new: async_add_entities(new)
        
    coordinator.async_add_listener(_update)
    _update()


class AirplanesLiveTracker(CoordinatorEntity, TrackerEntity):
    has_entity_name = True

    def __init__(self, coordinator, hex_id):
        super().__init__(coordinator)
        self._hex_id = hex_id
        self._attr_unique_id = f"airplanes_live_{self._hex_id}"
        
        ac_data = self._ac()
        callsign = ac_data.get("flight", "").strip() or self._hex_id
        self._attr_name = f"Tracked Flight {callsign}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Airplanes.Live Tracker",
            manufacturer="Airplanes.Live",
            model="ADS-B Client",
        )

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

        if "heli" in ac_type or "rotor" in ac_type: return "mdi:helicopter"
        if "glider" in ac_type: return "mdi:paper-airplane"
        if "balloon" in ac_type: return "mdi:hot-air-balloon"

        if baro_rate > 250: return "mdi:airplane-takeoff"
        elif baro_rate < -250: return "mdi:airplane-landing"
        return "mdi:airplane"

    @property
    def entity_picture(self):
        icao_type = self._ac().get("t")
        if icao_type: return f"/local/airplanes/{icao_type.upper()}.png"
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