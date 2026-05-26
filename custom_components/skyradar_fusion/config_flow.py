"""Config flow for SkyRadar Fusion."""

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
    CONF_GLOBAL_EMERGENCY,
    CONF_GLOBAL_MILITARY,
    MODE_SINGLE,
    MODE_ZONE,
)

CONF_ENABLE_FR24_ENRICHMENT = "enable_fr24_enrichment"


class SkyRadarFusionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SkyRadarFusionOptionsFlow(config_entry)

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


class SkyRadarFusionOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        options = dict(self._config_entry.options)

        if user_input is not None:
            options[CONF_LATITUDE] = user_input.get(CONF_LATITUDE)
            options[CONF_LONGITUDE] = user_input.get(CONF_LONGITUDE)
            options[CONF_RADIUS] = user_input.get(
                CONF_RADIUS, options.get(CONF_RADIUS, 5000)
            )
            options[CONF_GLOBAL_EMERGENCY] = user_input.get(
                CONF_GLOBAL_EMERGENCY, False
            )
            options[CONF_GLOBAL_MILITARY] = user_input.get(CONF_GLOBAL_MILITARY, False)
            options[CONF_ENABLE_FR24_ENRICHMENT] = user_input.get(
                CONF_ENABLE_FR24_ENRICHMENT, False
            )

            return self.async_create_entry(title="", data=options)

        entry = getattr(self, "config_entry", self._config_entry)

        current_lat = options.get(
            CONF_LATITUDE, entry.data.get(CONF_LATITUDE, self.hass.config.latitude)
        )
        current_lon = options.get(
            CONF_LONGITUDE, entry.data.get(CONF_LONGITUDE, self.hass.config.longitude)
        )
        current_radius = options.get(CONF_RADIUS, entry.data.get(CONF_RADIUS, 5000))

        schema_dict = {
            vol.Required(CONF_LATITUDE, default=current_lat): cv.latitude,
            vol.Required(CONF_LONGITUDE, default=current_lon): cv.longitude,
            vol.Required(CONF_RADIUS, default=current_radius): int,
            vol.Optional(
                CONF_GLOBAL_EMERGENCY, default=options.get(CONF_GLOBAL_EMERGENCY, False)
            ): bool,
            vol.Optional(
                CONF_GLOBAL_MILITARY, default=options.get(CONF_GLOBAL_MILITARY, False)
            ): bool,
            vol.Optional(
                CONF_ENABLE_FR24_ENRICHMENT,
                default=options.get(CONF_ENABLE_FR24_ENRICHMENT, False),
            ): bool,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema_dict))
