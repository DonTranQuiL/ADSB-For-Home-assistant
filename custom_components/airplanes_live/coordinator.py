"""DataUpdateCoordinator for Airplanes.Live."""

import logging
import math
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import AirplanesLiveAPI
from .const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_TRACKED_LIST,
    MODE_ZONE,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3440.065
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AirplanesLiveCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.config_entry = config_entry
        self.api = AirplanesLiveAPI(async_get_clientsession(hass))
        self.mode = config_entry.data.get(CONF_TRACKING_MODE, MODE_ZONE)

        self.previous_hexes = None
        self.entered_area = 0
        self.exited_area = 0

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    def classify_aircraft(self, ac):
        desc = ac.get("desc", "").lower()

        if "heli" in desc or "rotor" in desc:
            return "helicopter"

        if "military" in desc:
            return "military"

        if ac.get("flight", "").startswith(("KLM", "PH", "TRA")):
            return "commercial"

        return "private"

    async def _async_update_data(self):
        try:
            radius_meters = self.config_entry.options.get(
                CONF_RADIUS, self.config_entry.data.get(CONF_RADIUS, 5000)
            )
            tracked_list = self.config_entry.options.get(CONF_TRACKED_LIST, [])

            cat_counts = {"helicopter": 0, "military": 0, "commercial": 0, "private": 0}
            closest_aircraft = None
            closest_distance_meters = float("inf")
            filtered_aircraft = []
            current_hexes = set()

            if self.mode == MODE_ZONE:
                lat = self.config_entry.data.get(
                    CONF_LATITUDE, self.hass.config.latitude
                )
                lon = self.config_entry.data.get(
                    CONF_LONGITUDE, self.hass.config.longitude
                )
                radius_nm = max(1, math.ceil(radius_meters / 1852.0))
                aircraft_list = (
                    await self.api.get_aircraft_in_zone(lat, lon, radius_nm) or []
                )

                for ac in aircraft_list:
                    ac_lat = ac.get("lat")
                    ac_lon = ac.get("lon")
                    if ac_lat is None or ac_lon is None:
                        continue

                    dist_meters = haversine_distance(lat, lon, ac_lat, ac_lon) * 1852.0

                    if dist_meters <= radius_meters:
                        current_hexes.add(ac.get("hex"))
                        cat = self.classify_aircraft(ac)
                        ac["air_category"] = cat
                        ac["distance_meter"] = round(dist_meters, 1)
                        cat_counts[cat] += 1
                        filtered_aircraft.append(ac)

                        if dist_meters < closest_distance_meters:
                            closest_distance_meters = dist_meters
                            closest_aircraft = ac

            # Entered & Exited logic
            if self.previous_hexes is not None:
                self.entered_area = len(current_hexes - self.previous_hexes)
                self.exited_area = len(self.previous_hexes - current_hexes)
            self.previous_hexes = current_hexes

            # Specifiek Tracked Vliegtuigen (FR24 Style)
            tracked_aircraft_data = []
            for identifier in tracked_list:
                found = next(
                    (
                        ac
                        for ac in filtered_aircraft
                        if ac.get("flight", "").strip() == identifier
                        or ac.get("hex") == identifier
                    ),
                    None,
                )
                if not found:
                    res = await self.api.get_aircraft_by_callsign(identifier)
                    if not res:
                        res = await self.api.get_aircraft_by_hex(identifier)
                    if res:
                        ac = res[0]
                        ac["air_category"] = self.classify_aircraft(ac)
                        tracked_aircraft_data.append(ac)
                else:
                    tracked_aircraft_data.append(found)

            return {
                "aircraft": filtered_aircraft,
                "tracked_aircraft": tracked_aircraft_data,
                "total": len(filtered_aircraft),
                "counts": cat_counts,
                "closest": closest_aircraft,
                "entered": self.entered_area,
                "exited": self.exited_area,
                "additional_tracked": len(tracked_aircraft_data),
            }
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")
