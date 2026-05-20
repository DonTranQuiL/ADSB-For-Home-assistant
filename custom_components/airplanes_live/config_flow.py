"""Config flow for Airplanes.Live Tracker."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    CONF_TRACKING_MODE,
    CONF_RADIUS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_IDENTIFIER_TYPE,
    CONF_IDENTIFIER,
    CONF_TRACKED_LIST,
    CONF_ADD_TRACK,
    CONF_REMOVE_TRACK,
    CONF_CLEAR_TRACK,
    MODE_SINGLE,
    MODE_ZONE,
)


class AirplanesLiveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AirplanesLiveOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input[CONF_TRACKING_MODE] == MODE_ZONE:
                return await self.async_step_zone()
            return await self.async_step_single()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRACKING_MODE, default=MODE_ZONE): vol.In(
                        {MODE_ZONE: "Zone Tracking", MODE_SINGLE: "Target Tracking"}
                    )
                }
            ),
        )

    async def async_step_zone(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Zone Tracking",
                data={CONF_TRACKING_MODE: MODE_ZONE, **user_input},
            )
        return self.async_show_form(
            step_id="zone",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): cv.latitude,
                    vol.Required(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): cv.longitude,
                    vol.Required(CONF_RADIUS, default=5000): int,
                }
            ),
        )

    async def async_step_single(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Target Tracker",
                data={CONF_TRACKING_MODE: MODE_SINGLE, **user_input},
            )
        return self.async_show_form(
            step_id="single",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IDENTIFIER_TYPE, default="callsign"): vol.In(
                        {
                            "callsign": "Callsign",
                            "reg": "Registration",
                            "hex": "ICAO Hex",
                        }
                    ),
                    vol.Required(CONF_IDENTIFIER): str,
                }
            ),
        )


class AirplanesLiveOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        options = dict(self._config_entry.options)
        tracked_list = options.get(CONF_TRACKED_LIST, [])

        if user_input is not None:
            # Voeg specifiek vliegtuig toe
            add_track = user_input.get(CONF_ADD_TRACK, "").strip().upper()
            if add_track and add_track not in tracked_list:
                tracked_list.append(add_track)

            # Verwijder specifiek vliegtuig
            remove_track = user_input.get(CONF_REMOVE_TRACK, "").strip().upper()
            if remove_track in tracked_list:
                tracked_list.remove(remove_track)

            # Wis de hele lijst
            if user_input.get(CONF_CLEAR_TRACK, False):
                tracked_list = []

            options[CONF_RADIUS] = user_input.get(
                CONF_RADIUS, options.get(CONF_RADIUS, 5000)
            )
            options[CONF_TRACKED_LIST] = tracked_list

            return self.async_create_entry(title="", data=options)

        current_radius = options.get(
            CONF_RADIUS, self._config_entry.data.get(CONF_RADIUS, 5000)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RADIUS, default=current_radius): int,
                    vol.Optional(CONF_ADD_TRACK, default=""): str,
                    vol.Optional(CONF_REMOVE_TRACK, default=""): str,
                    vol.Optional(CONF_CLEAR_TRACK, default=False): bool,
                }
            ),
        )
