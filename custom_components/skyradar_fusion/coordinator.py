import logging
from datetime import timedelta
import math
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import SkyRadarFusionAPI
from .const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_GLOBAL_EMERGENCY,
    CONF_GLOBAL_MILITARY,
    MODE_ZONE,
    DEFAULT_SCAN_INTERVAL,
)

CONF_ENABLE_FR24_ENRICHMENT = "enable_fr24_enrichment"

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

# AANGEPAST: De Class naam is nu SkyRadarFusionCoordinator
class SkyRadarFusionCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config_entry):
        self.config_entry = config_entry
        # AANGEPAST: Gebruikt nu de SkyRadarFusionAPI
        self.api = SkyRadarFusionAPI(async_get_clientsession(hass), hass)
        self.mode = config_entry.data.get(CONF_TRACKING_MODE, MODE_ZONE)

        self.previous_hexes = None
        self.entered_area = 0
        self.exited_area = 0

        self.tracked_list = set()
        self.consecutive_errors = 0
        self.last_update_status = "Pending"
        self.last_update_time = None
        self.photo_cache = {}
        self.fr24_cache = {}

        state_obj = hass.states.get("sensor.skyradar_fusion_additional_tracked")
        if state_obj:
            saved_list = state_obj.attributes.get("tracking_list")
            if saved_list:
                for item in str(saved_list).split(","):
                    if item.strip():
                        self.add_track(item.strip())
            elif state_obj.state and not state_obj.state.isdigit() and state_obj.state not in ["unknown", "unavailable"]:
                for item in str(state_obj.state).split(","):
                    if item.strip():
                        self.add_track(item.strip())

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    def add_track(self, identifier):
        if identifier:
            clean_id = identifier.strip().upper().replace(" ", "")
            self.tracked_list.add(clean_id)
            _LOGGER.info("SkyRadar Fusion: Target '%s' added to tracking list.", clean_id)

    def remove_track(self, identifier):
        if identifier:
            clean_id = identifier.strip().upper().replace(" ", "")
            self.tracked_list.discard(clean_id)
            _LOGGER.info("SkyRadar Fusion: Target '%s' removed from tracking list.", clean_id)

    def clear_tracks(self):
        self.tracked_list.clear()

    def clean_aircraft_data(self, ac):
        keys_to_keep = [
            "hex", "flight", "r", "t", "desc", "alt_baro", "gs", "ias", "tas", "mach", 
            "track", "roll", "mag_heading", "true_heading", "baro_rate", "squawk", 
            "emergency", "category", "nav_altitude_mcp", "lat", "lon", "oat", "tat"
        ]
        cleaned = {
            k: ac.get(k) for k in keys_to_keep if k in ac and ac.get(k) is not None
        }
        cleaned["air_category"] = self.classify_aircraft(ac)
        return cleaned

    def classify_aircraft(self, ac):
        desc = ac.get("desc", "").lower()
        flight = ac.get("flight", "").strip().upper()
        cat = ac.get("category", "").strip().upper()

        if "heli" in desc or "rotor" in desc or cat == "A7":
            return "helicopter"
        if "military" in desc or "mil" in desc or cat == "A6":
            return "military"

        if flight:
            if re.match(r"^[A-Z]{3}\d", flight):
                return "commercial"
            commercial_prefixes = (
                "NJE", "EJA", "VJT", "FLX", "WUP", "AHO", "GAC", "QQE", "LUX", "TAG", 
                "EJM", "CLY", "SLR", "JAS", "CLA", "DCS", "JFA", "FLY", "FYG", "SVW", 
                "XGO", "AWC", "HFY", "LYX", "TVS", "EXS", "TOM", "TUI", "CND", "MPH", 
                "BTI", "FDX", "UPS", "DHL", "BCS", "BOX", "GTI", "PAC", "CKS", "TAY", 
                "CCX", "KLM", "PH", "TRA"
            )
            if flight.startswith(commercial_prefixes):
                return "commercial"

        if cat in ["A3", "A4", "A5"]:
            return "commercial"

        return "private"

    async def _fetch_photo_background(self, reg, hex_code, cache_key):
        photo_url = await self.api.get_planespotters_photo(reg, hex_code)
        if photo_url:
            self.photo_cache[cache_key] = photo_url
        else:
            self.photo_cache[cache_key] = "None"

    async def _fetch_fr24_background(self, search_id):
        try:
            fr24_data = await self.api.get_fr24_enrichment(search_id)
            if fr24_data:
                self.fr24_cache[search_id] = fr24_data
            else:
                self.fr24_cache[search_id] = "None"
        except Exception:
            self.fr24_cache[search_id] = "None"

    async def _async_update_data(self):
        try:
            radius_meters = self.config_entry.options.get(CONF_RADIUS, self.config_entry.data.get(CONF_RADIUS, 5000))
            enable_emergencies = self.config_entry.options.get(CONF_GLOBAL_EMERGENCY, False)
            enable_military = self.config_entry.options.get(CONF_GLOBAL_MILITARY, False)
            enable_fr24 = self.config_entry.options.get(CONF_ENABLE_FR24_ENRICHMENT, False)

            home_lat = self.config_entry.options.get(CONF_LATITUDE, self.config_entry.data.get(CONF_LATITUDE, self.hass.config.latitude))
            home_lon = self.config_entry.options.get(CONF_LONGITUDE, self.config_entry.data.get(CONF_LONGITUDE, self.hass.config.longitude))

            cat_counts = {"helicopter": 0, "military": 0, "commercial": 0, "private": 0}
            closest_aircraft = None
            closest_distance_meters = float("inf")
            filtered_aircraft = []
            current_hexes = set()
            global_emergencies_data = []
            global_military_data = []

            if self.mode == MODE_ZONE:
                radius_nm = max(1, math.ceil(radius_meters / 1852.0))
                aircraft_list = await self.api.get_aircraft_in_zone(home_lat, home_lon, radius_nm)
                
                if aircraft_list is None:
                    if self.data:
                        filtered_aircraft = self.data.get("aircraft", [])
                        cat_counts = self.data.get("counts", cat_counts)
                        closest_aircraft = self.data.get("closest", None)
                        current_hexes = self.previous_hexes or set()
                else:
                    for ac in aircraft_list:
                        ac_lat, ac_lon = ac.get("lat"), ac.get("lon")
                        if ac_lat is None or ac_lon is None:
                            continue

                        dist_meters = haversine_distance(home_lat, home_lon, ac_lat, ac_lon) * 1852.0

                        if dist_meters <= radius_meters:
                            current_hexes.add(ac.get("hex"))
                            clean_ac = self.clean_aircraft_data(ac)
                            clean_ac["distance_meter"] = round(dist_meters, 1)
                            cat_counts[clean_ac["air_category"]] += 1
                            filtered_aircraft.append(clean_ac)

                            if dist_meters < closest_distance_meters:
                                closest_distance_meters = dist_meters
                                closest_aircraft = clean_ac

            if self.previous_hexes is not None:
                self.entered_area = len(current_hexes - self.previous_hexes)
                self.exited_area = len(self.previous_hexes - current_hexes)
            self.previous_hexes = current_hexes

            if enable_emergencies:
                em_raw = await self.api.get_global_emergencies()

                if em_raw is None or (len(em_raw) == 0 and self.data and len(self.data.get("global_emergencies", [])) > 0):
                    global_emergencies_data = self.data.get("global_emergencies", []) if self.data else []
                else:
                    for ac in em_raw:
                        clean_ac = self.clean_aircraft_data(ac)
                        if clean_ac.get("lat") and clean_ac.get("lon"):
                            clean_ac["distance_meter"] = round(haversine_distance(home_lat, home_lon, clean_ac["lat"], clean_ac["lon"]) * 1852.0, 1)
                        global_emergencies_data.append(clean_ac)

            if enable_military:
                mil_raw = await self.api.get_global_military()
                if mil_raw is None or (len(mil_raw) == 0 and self.data and len(self.data.get("global_military", [])) > 0):
                    global_military_data = self.data.get("global_military", []) if self.data else []
                else:
                    for ac in mil_raw:
                        clean_ac = self.clean_aircraft_data(ac)
                        if clean_ac.get("lat") and clean_ac.get("lon"):
                            clean_ac["distance_meter"] = round(haversine_distance(home_lat, home_lon, clean_ac["lat"], clean_ac["lon"]) * 1852.0, 1)
                        global_military_data.append(clean_ac)

            tracked_aircraft_data = []
            for identifier in self.tracked_list:
                found = next(
                    (ac for ac in filtered_aircraft + global_emergencies_data + global_military_data if ac.get("flight", "").strip().upper() == identifier or ac.get("hex", "").upper() == identifier),
                    None,
                )
                if not found:
                    res = await self.api.get_aircraft_by_callsign(identifier) or await self.api.get_aircraft_by_hex(identifier)
                    if res:
                        tracked_aircraft_data.append(self.clean_aircraft_data(res[0]))
                    else:
                        tracked_aircraft_data.append({
                            "hex": identifier, 
                            "flight": identifier,
                            "air_category": "Unknown",
                            "distance_meter": "N/A"
                        })
                else:
                    tracked_aircraft_data.append(found)

            all_active_targets = tracked_aircraft_data + global_emergencies_data + global_military_data + ([closest_aircraft] if closest_aircraft else [])
            
            unique_targets = {target.get("hex"): target for target in all_active_targets}.values()

            for target in unique_targets:
                reg = target.get("r") or "Unknown"
                hex_code = target.get("hex") or "Unknown"
                callsign = target.get("flight", "").strip().upper()

                cache_key = hex_code if hex_code != "Unknown" else reg

                if cache_key != "Unknown" and cache_key not in self.photo_cache:
                    self.photo_cache[cache_key] = "Loading"
                    self.hass.async_create_task(self._fetch_photo_background(reg, hex_code, cache_key))
                
                if enable_fr24:
                    search_id = callsign if callsign else reg
                    if search_id and search_id != "Unknown":
                        if search_id not in self.fr24_cache:
                            self.fr24_cache[search_id] = "Loading"
                            self.hass.async_create_task(self._fetch_fr24_background(search_id))

            for target in filtered_aircraft + list(unique_targets):
                reg = target.get("r") or "Unknown"
                hex_code = target.get("hex") or "Unknown"
                callsign = target.get("flight", "").strip().upper()
                
                cache_key = hex_code if hex_code != "Unknown" else reg
                if self.photo_cache.get(cache_key) and self.photo_cache[cache_key] not in ["None", "Loading"]:
                    target["api_photo_url"] = self.photo_cache[cache_key]

                if enable_fr24:
                    search_id = callsign if callsign else reg
                    fr24_data = self.fr24_cache.get(search_id)
                    if fr24_data and isinstance(fr24_data, dict):
                        target.update(fr24_data)
                        if fr24_data.get("fr24_photo"):
                            target["api_photo_url"] = fr24_data["fr24_photo"]

            self.consecutive_errors = 0
            self.last_update_status = "Success"
            self.last_update_time = dt_util.now()

            return {
                "aircraft": filtered_aircraft,
                "tracked_aircraft": list(unique_targets),
                "global_emergencies": global_emergencies_data,
                "global_military": global_military_data,
                "total": len(filtered_aircraft),
                "counts": cat_counts,
                "closest": closest_aircraft,
                "entered": self.entered_area,
                "exited": self.exited_area,
                "additional_tracked": len(self.tracked_list), 
                "tracking_list": ",".join(self.tracked_list) if self.tracked_list else "",
            }
        
        except Exception as err:
            self.consecutive_errors += 1
            self.last_update_status = "Failed"
            self.last_update_time = dt_util.now()
            
            if self.data:
                _LOGGER.debug("API error. using frozen data instead...")
                return self.data
                
            raise UpdateFailed(f"Error fetching data: {err}")