"""The eSolat Takwim Malaysia integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import aiofiles.os
import logging

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up eSolat Takwim Malaysia from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up storage files."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        prayer_times_file = hass.config.path("storage", "esolat_prayer_times.json")
        events_file = hass.config.path("storage", "esolat_events.json")
        
        for file_path in (prayer_times_file, events_file):
            if await aiofiles.os.path.exists(file_path):
                try:
                    await aiofiles.os.remove(file_path)
                    _LOGGER.debug("Removed storage file %s", file_path)
                except OSError as err:
                    _LOGGER.warning("Failed to remove storage file %s: %s", file_path, err)

        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok