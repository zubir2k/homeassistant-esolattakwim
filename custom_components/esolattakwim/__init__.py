"""The eSolat Takwim Malaysia integration."""
from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import LEGACY_STORAGE_KEYS, TakwimConfigEntry, TakwimCoordinator, cache_store

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: TakwimConfigEntry) -> bool:
    """Set up eSolat Takwim Malaysia from a config entry."""
    # Caches from v0.3.x are replaced by esolattakwim.cache
    for key in LEGACY_STORAGE_KEYS:
        await cache_store(hass, key).async_remove()

    coordinator = TakwimCoordinator(hass, entry)
    # Raises ConfigEntryNotReady (HA retries) only when there is no stored timetable and JAKIM is down
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_entry_updated(hass: HomeAssistant, entry: TakwimConfigEntry) -> None:
    """A new zone is picked up by reloading; the cache notices the change and refetches."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: TakwimConfigEntry) -> bool:
    """Unload; the stored timetable stays so a reload or restart needs no download."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: TakwimConfigEntry) -> None:
    """Removing the integration deletes its stored timetable."""
    await cache_store(hass).async_remove()
