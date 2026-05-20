"""Sensor platform for Airplanes.Live."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, MODE_ZONE

CATEGORIES = ["helicopter", "military", "commercial", "private"]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Airplanes.Live sensors."""
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
    """Base class for Airplanes.Live sensors to handle device grouping."""
    has_entity_name = True

    def __init__(self, coordinator):
        """Initialize the sensor base."""
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
    """Sensor that summarizes the total airspace."""
    
    def __init__(self, coordinator):
        """Initialize the overview sensor."""
        super().__init__(coordinator)
        self._attr_name = "Current in area"
        self._attr_unique_id = f"airspace_overview_{coordinator.config_entry.entry_id}"
        self._attr_icon = "mdi:radar"
    
    @property
    def native_value(self): 
        return self.coordinator.data.get("total", 0)

    @property
    def extra_state_attributes(self):
        """Return closest aircraft details AND the full list of aircraft."""
        attrs = {}
        
        # 1. De Dichtstbijzijnde (Bestaande logica)
        closest = self.coordinator.data.get("closest")
        if closest:
            attrs["Closest Flight"] = closest.get("flight", "").strip() or "Unknown"
            attrs["Closest Distance (m)"] = closest.get("distance_meter")
            attrs["Closest Type"] = closest.get("desc")
            attrs["Closest Altitude"] = closest.get("alt_baro")
        else:
            attrs["Closest Flight"] = "None"
            
        # 2. NIEUW: De Volledige Lijst! (Dit is wat de tester vroeg)
        attrs["flights_list"] = self.coordinator.data.get("aircraft", [])
        
        return attrs


class AirplanesLiveCategorySensor(AirplanesLiveSensorBase):
    """Sensor for specific category counts like Helicopters or Military."""
    
    def __init__(self, coordinator, category):
        """Initialize the category sensor."""
        super().__init__(coordinator)
        self._category = category
        self._attr_name = f"{category.capitalize()}s in area"
        self._attr_unique_id = f"airplanes_live_{category}_{coordinator.config_entry.entry_id}"
        self._attr_icon = "mdi:helicopter" if category == "helicopter" else "mdi:airplane"
    
    @property
    def native_value(self): 
        return self.coordinator.data.get("counts", {}).get(self._category, 0)
        
    @property
    def extra_state_attributes(self):
        """Return active flight list for this specific category."""
        flights = [
            ac.get("flight", "").strip() 
            for ac in self.coordinator.data.get("aircraft", []) 
            if ac.get("air_category") == self._category
        ]
        return {"Active Flights": flights if flights else "None"}
