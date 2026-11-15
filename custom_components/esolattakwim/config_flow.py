"""Config flow for eSolat Takwim Malaysia."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import DOMAIN, ZONES

DEFAULT_ZONE = "sgr01"


def _schema(zone: str) -> vol.Schema:
    return vol.Schema({vol.Required("zone", default=zone): vol.In(ZONES)})


class EsolatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pick the JAKIM zone."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="eSolat Takwim Malaysia", data={"zone": user_input["zone"]})
        return self.async_show_form(step_id="user", data_schema=_schema(DEFAULT_ZONE))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguring the zone."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data={**entry.data, "zone": user_input["zone"]},
                reason="reconfigure_successful",
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(entry.data.get("zone", DEFAULT_ZONE)),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlow):
    """Change the zone; the entry reloads and fetches the new zone's year."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            if user_input["zone"] != self.config_entry.data.get("zone"):
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data={**self.config_entry.data, "zone": user_input["zone"]}
                )
            return self.async_create_entry(data={})
        return self.async_show_form(
            step_id="init", data_schema=_schema(self.config_entry.data.get("zone", DEFAULT_ZONE))
        )
