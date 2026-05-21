"""Sensor platform for Airplanes.Live."""

from homeassistant.components.sensor import SensorEntity, RestoreSensor
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.const import EntityCategory
from .const import DOMAIN, MODE_ZONE, CONF_GLOBAL_EMERGENCY, CONF_GLOBAL_MILITARY

CATEGORIES = ["helicopter", "military", "commercial", "private"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        AirplanesLiveOverviewSensor(coordinator),
        AirplanesLiveStatSensor(
            coordinator, "entered", "Entered area", "mdi:airplane-takeoff"
        ),
        AirplanesLiveStatSensor(
            coordinator, "exited", "Exited area", "mdi:airplane-landing"
        ),
        AirplanesLiveTrackedRestoreSensor(
            coordinator
        ),  # De slimme memory-herstelsensor
        # NIEUW: Diagnostische Sensoren!
        AirplanesLiveDiagnosticSensor(
            coordinator,
            "consecutive_errors",
            "Consecutive Errors",
            "mdi:alert-circle-outline",
        ),
        AirplanesLiveDiagnosticSensor(
            coordinator,
            "last_update_status",
            "Last Update Status",
            "mdi:check-network-outline",
        ),
        AirplanesLiveDiagnosticSensor(
            coordinator,
            "last_update_time",
            "Last Update Time",
            "mdi:clock-outline",
            "timestamp",
        ),
    ]

    if config_entry.data.get("tracking_mode") == MODE_ZONE:
        for cat in CATEGORIES:
            entities.append(AirplanesLiveCategorySensor(coordinator, cat))

    if config_entry.options.get(CONF_GLOBAL_EMERGENCY, False):
        entities.append(
            AirplanesLiveGlobalSensor(
                coordinator,
                "global_emergencies",
                "Global Emergencies (7700)",
                "mdi:alert-decagram",
            )
        )

    if config_entry.options.get(CONF_GLOBAL_MILITARY, False):
        entities.append(
            AirplanesLiveGlobalSensor(
                coordinator, "global_military", "Global Military", "mdi:fighter-jet"
            )
        )

    async_add_entities(entities)


class AirplanesLiveSensorBase(CoordinatorEntity, SensorEntity):
    has_entity_name = True

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Airplanes.Live Tracker",
        )


class AirplanesLiveTrackedRestoreSensor(AirplanesLiveSensorBase, RestoreSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Additional tracked"
        self._attr_icon = "mdi:radar"
        self._attr_unique_id = (
            f"airplanes_live_additional_tracked_{coordinator.config_entry.entry_id}"
        )

    @property
    def native_value(self):
        return (
            self.coordinator.data.get("additional_tracked", 0)
            if self.coordinator.data
            else 0
        )

    @property
    def extra_state_attributes(self):
        return {"tracking_list": list(self.coordinator.tracked_list)}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and "tracking_list" in last_state.attributes:
            for identifier in last_state.attributes["tracking_list"]:
                self.coordinator.add_track(identifier)


# --- Diagnostic Sensors ---
class AirplanesLiveDiagnosticSensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator, key, name, icon, device_class=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = (
            f"airplanes_live_{key}_{coordinator.config_entry.entry_id}"
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if device_class:
            self._attr_device_class = device_class

    @property
    def native_value(self):
        return getattr(self.coordinator, self._key, None)


# --- Old known sensors ---
class AirplanesLiveStatSensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator, stat_type, name, icon):
        super().__init__(coordinator)
        self._stat_type = stat_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = (
            f"airplanes_live_{stat_type}_{coordinator.config_entry.entry_id}"
        )

    @property
    def native_value(self):
        return (
            self.coordinator.data.get(self._stat_type, 0)
            if self.coordinator.data
            else 0
        )


class AirplanesLiveOverviewSensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current in area"
        self._attr_unique_id = f"airspace_overview_{coordinator.config_entry.entry_id}"
        self._attr_icon = "mdi:radar"

    @property
    def native_value(self):
        return self.coordinator.data.get("total", 0) if self.coordinator.data else 0

    @property
    def extra_state_attributes(self):
        attrs = {}
        if not self.coordinator.data:
            return {"Closest Flight": "None", "flights_list": []}

        closest = self.coordinator.data.get("closest")
        if closest:
            attrs["Closest Flight"] = closest.get("flight", "").strip() or "Unknown"
            attrs["Closest Distance (m)"] = closest.get("distance_meter")
            attrs["Closest Type"] = closest.get("desc")
            attrs["Closest Altitude"] = closest.get("alt_baro")
        else:
            attrs["Closest Flight"] = "None"

        attrs["flights_list"] = self.coordinator.data.get("aircraft", [])
        return attrs


class AirplanesLiveCategorySensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator, category):
        super().__init__(coordinator)
        self._category = category
        self._attr_name = f"{category.capitalize()}s in area"
        self._attr_unique_id = (
            f"airplanes_live_{category}_{coordinator.config_entry.entry_id}"
        )
        self._attr_icon = (
            "mdi:helicopter" if category == "helicopter" else "mdi:airplane"
        )

    @property
    def native_value(self):
        return (
            self.coordinator.data.get("counts", {}).get(self._category, 0)
            if self.coordinator.data
            else 0
        )


class AirplanesLiveGlobalSensor(AirplanesLiveSensorBase):
    def __init__(self, coordinator, data_key, name, icon):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = (
            f"airplanes_live_{data_key}_{coordinator.config_entry.entry_id}"
        )

    @property
    def native_value(self):
        return (
            len(self.coordinator.data.get(self._data_key, []))
            if self.coordinator.data
            else 0
        )

    @property
    def extra_state_attributes(self):
        return {
            "flights_list": self.coordinator.data.get(self._data_key, [])
            if self.coordinator.data
            else []
        }
