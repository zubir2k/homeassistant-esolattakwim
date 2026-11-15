"""Sensor platform for eSolat Takwim Malaysia."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import DOMAIN, HIJRI_MONTHS, PRAYER_NAMES, TIMEZONE
from .coordinator import TakwimConfigEntry, TakwimCoordinator
from .entity import TakwimEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: TakwimConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [HijriSensor(coordinator, entry.entry_id)]
        + [PrayerTimeSensor(coordinator, entry.entry_id, prayer) for prayer in PRAYER_NAMES]
    )


def hijri_text(raw: str | None) -> str | None:
    """'1448-05-20' -> '20 Jamadil Awwal 1448'."""
    try:
        year, month, day = (raw or "").split("-")
        return f"{int(day):02d} {HIJRI_MONTHS[month]} {year}"
    except (ValueError, KeyError):
        return None


class _DailySensor(TakwimEntity, SensorEntity):
    """Re-renders just after midnight, when 'today' moves on, without any API call."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _midnight(_now: datetime) -> None:
            self.async_write_ha_state()

        self.async_on_remove(async_track_time_change(self.hass, _midnight, hour=0, minute=0, second=1))


class PrayerTimeSensor(_DailySensor):
    """Today's time for one prayer (sensor.esolat_takwim_fajr)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:star-crescent"

    def __init__(self, coordinator: TakwimCoordinator, entry_id: str, prayer: str) -> None:
        super().__init__(coordinator)
        self._prayer = prayer
        self._attr_name = prayer.capitalize()
        self._attr_translation_key = prayer
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{prayer}"
        self.entity_id = f"sensor.esolat_takwim_{prayer}"

    def _at(self) -> datetime | None:
        return self.coordinator.prayer_times(dt_util.now(TIMEZONE).date()).get(self._prayer)

    @property
    def native_value(self) -> datetime | None:
        at = self._at()
        return dt_util.as_utc(at) if at else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        at = self._at()
        if at is None:
            return {"time_12h": "Unknown", "time_24h": "Unknown"}
        return {"time_12h": at.strftime("%I:%M %p"), "time_24h": at.strftime("%H:%M")}


class HijriSensor(_DailySensor):
    """Today's Hijri date as published by JAKIM."""

    _attr_icon = "mdi:calendar"
    _attr_name = "Hijri Date"

    def __init__(self, coordinator: TakwimCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = "hijri"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_hijri"
        self.entity_id = "sensor.esolat_takwim_hijri"

    def _raw(self) -> str | None:
        return self.coordinator.day(dt_util.now(TIMEZONE).date()).get("hijri") or None

    @property
    def native_value(self) -> str | None:
        return hijri_text(self._raw())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"date": self._raw() or "Unknown"}
