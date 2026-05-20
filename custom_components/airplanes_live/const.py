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

# Nieuwe FR24-stijl opties
CONF_TRACKED_LIST = "tracked_list"
CONF_ADD_TRACK = "add_track"
CONF_REMOVE_TRACK = "remove_track"
CONF_CLEAR_TRACK = "clear_track"

MODE_SINGLE = "single_aircraft"
MODE_ZONE = "zone_radius"

DEFAULT_SCAN_INTERVAL = 10 
PLATFORMS = ["sensor", "device_tracker"]