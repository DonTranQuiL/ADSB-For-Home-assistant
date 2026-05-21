"""Constants for the Airplanes.Live integration."""
from datetime import timedelta

DOMAIN = "airplanes_live"
NAME = "Airplanes.Live Tracker"

API_BASE_URL = "https://api.airplanes.live/v2"

CONF_TRACKING_MODE = "tracking_mode"
CONF_IDENTIFIER_TYPE = "identifier_type"
CONF_IDENTIFIER = "identifier"
CONF_RADIUS = "radius"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

CONF_TRACKED_LIST = "tracked_list"
CONF_GLOBAL_EMERGENCY = "global_emergency"
CONF_GLOBAL_MILITARY = "global_military"

# De missende sleutel voor de Device Trackers:
CONF_ENABLE_TRACKER = "enable_tracker"

MODE_SINGLE = "single_aircraft"
MODE_ZONE = "zone_radius"

DEFAULT_SCAN_INTERVAL = 10 
PLATFORMS = ["sensor", "device_tracker", "text", "button"]