"""Sensor platform for Airplanes.Live."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, MODE_ZONE

CATEGORIES = ["helicopter", "military", "commercial", "private"]

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        AirplanesLiveOverviewSensor(coordinator),
        AirplanesLiveStatSensor(coordinator, "entered", "Entered area", "mdi:airplane-takeoff"),
        AirplanesLiveStatSensor(coordinator, "exited", "Exited area", "mdi:airplane-landing"),
        AirplanesLiveStatSensor(coordinator, "additional_tracked", "Additional tracked", "mdi:radar")
    ]
    
    if config_entry.data.get("tracking_mode") == MODE_ZONE:
        for cat in CATEGORIES:
            entities.append(AirplanesLiveCategorySensor(coordinator, cat))
            
    async_add_entities(entities)


class AirplanesLiveSensorBase(CoordinatorEntity, SensorEntity):
    has_entity_name = True
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Airplanes.Live Tracker",
            manufacturer="Airplanes.Live",
            model="ADS-B Client",
        )

class AirplanesLiveStatSensor(AirplanesLiveSensorBase):
    """Dynamische sensor voor statistieken zoals Entered en Exited."""
    def __init__(self, coordinator, stat_type, name, icon):
        super().__init__(coordinator)
        self._stat_type = stat_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"airplanes_live_{stat_type}_{coordinator.config_entry.entry_id}"
        
    @property
    def native_value(self):
        return self.coordinator.data.get(self._stat_type, 0)

class AirplanesLiveOverviewSensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current in area"
        self._attr_unique_id = f"airspace_overview_{coordinator.config_entry.entry_id}"
        self._attr_icon = "mdi:radar"
    
    @property
    def native_value(self): 
        return self.coordinator.data.get("total", 0)

    @property
    def extra_state_attributes(self):
        closest = self.coordinator.data.get("closest")
        if closest:
            return {
                "Closest Flight": closest.get("flight", "").strip() or "Unknown",
                "Closest Distance (m)": closest.get("distance_meter"),
                "Closest Type": closest.get("desc"),
                "Closest Altitude": closest.get("alt_baro")
            }
        return {"Closest": "None"}


class AirplanesLiveCategorySensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator, category):
        super().__init__(coordinator)
        self._category = category
        self._attr_name = f"{category.capitalize()}s in area"
        self._attr_unique_id = f"airplanes_live_{category}_{coordinator.config_entry.entry_id}"
        self._attr_icon = "mdi:helicopter" if category == "helicopter" else "mdi:airplane"
    
    @property
    def native_value(self): 
        return self.coordinator.data.get("counts", {}).get(self._category, 0)