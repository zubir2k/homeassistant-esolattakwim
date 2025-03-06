"""Sensor platform for eSolat Takwim Malaysia."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, TIMEZONE, HIJRI_MONTHS
from .prayer_times import PrayerTimesData

_LOGGER = logging.getLogger(__name__)

PRAYER_SENSORS = ["imsak", "fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the eSolat Takwim Malaysia sensor platform."""
    zone = config_entry.data["zone"]
    prayer_times = PrayerTimesData(zone, hass)
    await prayer_times.load_cached_data()

    entities = [HijriSensor(hass, prayer_times, config_entry.entry_id)]
    entities.extend(PrayerTimeSensor(hass, prayer_times, prayer, config_entry.entry_id) for prayer in PRAYER_SENSORS)
    async_add_entities(entities, True)

class PrayerTimeSensor(SensorEntity):
    """Representation of a prayer time sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, prayer_times: PrayerTimesData, prayer: str, entry_id: str) -> None:
        """Initialize the prayer time sensor."""
        self.hass = hass
        self._prayer_times = prayer_times
        self._prayer = prayer
        self._attr_name = prayer.capitalize()
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{prayer}"
        self.entity_id = f"sensor.esolat_takwim_{prayer}"
        self._attr_icon = "mdi:star-crescent"
        self._state = None
        self._attributes = {}
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_registry_visible_default = True

    @property
    def state(self) -> str | None:
        """Return the state of the sensor (UTC timestamp)."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._attributes

    async def async_update(self) -> None:
        """Update the sensor state and attributes."""
        prayer_times = self._prayer_times.get_prayer_times_utc()
        utc_time = prayer_times.get(self._prayer)
        self._state = utc_time if utc_time else None
        if utc_time and utc_time != "unknown":
            local_dt = dt_util.parse_datetime(utc_time).astimezone(TIMEZONE)
            self._attributes = {
                "time_12h": local_dt.strftime("%I:%M %p"),
                "time_24h": local_dt.strftime("%H:%M"),
            }
        else:
            self._attributes = {"time_12h": "Unknown", "time_24h": "Unknown"}

class HijriSensor(SensorEntity):
    """Representation of a Hijri date sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar"

    def __init__(self, hass: HomeAssistant, prayer_times: PrayerTimesData, entry_id: str) -> None:
        """Initialize the Hijri date sensor."""
        self.hass = hass
        self._prayer_times = prayer_times
        self._attr_name = "Hijri Date"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_hijri"
        self.entity_id = f"sensor.esolat_takwim_hijri"
        self._attr_icon = "mdi:calendar"
        self._state = None
        self._attributes = {}
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_registry_visible_default = True

    @property
    def state(self) -> str | None:
        """Return the state of the sensor (full Hijri text)."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._attributes

    async def async_update(self) -> None:
        """Update the sensor state and attributes."""
        today_date = dt_util.now(TIMEZONE).strftime("%d-%b-%Y")
        today_prayer_times = self._prayer_times._daily_prayer_times.get(today_date, {})
        hijri_date = today_prayer_times.get("hijri")

        if hijri_date:
            hijri_year, hijri_month, hijri_day = hijri_date.split("-")
            month_name = HIJRI_MONTHS.get(hijri_month, "Unknown")
            self._state = f"{int(hijri_day):02d} {month_name} {hijri_year}"
            self._attributes = {"date": hijri_date}
        else:
            self._state = "Unknown"
            self._attributes = {"date": "Unknown"}