"""Config flow for eSolat Takwim Malaysia integration."""
from __future__ import annotations

import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, ZONES

_LOGGER = logging.getLogger(__name__)

class EsolatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for eSolat Takwim Malaysia."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="eSolat Takwim Malaysia",
                data={"zone": user_input["zone"]}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("zone", default="sgr01"): vol.In(ZONES)
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handle options flow for eSolat Takwim Malaysia."""

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            new_zone = user_input["zone"]
            _LOGGER.debug("Updating zone to %s", new_zone)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={"zone": new_zone}
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    "zone",
                    default=self.config_entry.data.get("zone", "sgr01")
                ): vol.In(ZONES)
            }),
            errors=errors,
        )