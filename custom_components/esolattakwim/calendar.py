"""Support for eSolat Takwim Malaysia Calendar."""
from __future__ import annotations

import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt
from homeassistant.helpers.storage import Store

from .const import DOMAIN, ISLAMIC_EVENTS_API, TIMEZONE, HIJRI_MONTHS, PRAYER_TIMES_API
from .prayer_times import PrayerTimesData

_LOGGER = logging.getLogger(__name__)

EVENTS_STORAGE_VERSION = 1
EVENTS_STORAGE_KEY = "esolat_events"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the eSolat Takwim Malaysia Calendar platform."""
    zone = config_entry.data["zone"]
    prayer_times = PrayerTimesData(zone, hass)
    calendar = EsolatCalendar(hass, zone, config_entry, prayer_times)
    await calendar.load_cached_data()
    hass.data[DOMAIN][config_entry.entry_id] = {"prayer_times": prayer_times}
    async_add_entities([calendar], True)

class EsolatCalendar(CalendarEntity):
    """eSolat calendar entity."""
    
    _attr_has_entity_name = True
    _attr_name = "eSolat Takwim"
    _attr_unique_id = "esolat_takwim"

    def __init__(self, hass: HomeAssistant, zone: str, config_entry: ConfigEntry, prayer_times: PrayerTimesData) -> None:
        """Initialize the calendar."""
        self.hass = hass
        self.zone = zone
        self._config_entry = config_entry
        self._prayer_times = prayer_times
        self._islamic_events: list[CalendarEvent] = []
        self._attr_extra_state_attributes = {
            "hijri_date": None,
            "hijri_full": None,
            "current": None,
            "next": None,
            "imsak": None,
            "fajr": None,
            "syuruk": None,
            "dhuhr": None,
            "asr": None,
            "maghrib": None,
            "isha": None,
            "zone": zone,
        }
        self._event_store = Store(hass, EVENTS_STORAGE_VERSION, EVENTS_STORAGE_KEY)
        self._config_entry.add_update_listener(self.async_config_entry_updated)

    async def async_config_entry_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle config entry updates."""
        new_zone = entry.data["zone"]
        if new_zone != self.zone:
            await self.update_zone(new_zone)
            await self.async_update_ha_state(force_refresh=True)

    async def update_zone(self, new_zone: str) -> None:
        """Update the zone and fetch new prayer times."""
        _LOGGER.debug("Updating zone from %s to %s", self.zone, new_zone)
        self.zone = new_zone
        self._attr_extra_state_attributes["zone"] = new_zone
        self._prayer_times = PrayerTimesData(new_zone, self.hass)
        hass.data[DOMAIN][self._config_entry.entry_id]["prayer_times"] = self._prayer_times
        async with aiohttp.ClientSession() as session:
            success = await self._prayer_times.fetch_prayer_times(session)
            if not success:
                _LOGGER.warning("Failed to fetch prayer times for zone %s, using empty data until next update", new_zone)

    async def load_cached_data(self) -> None:
        """Load cached Islamic events and prayer times on initial setup."""
        await self._prayer_times.load_cached_data()
        cached_events = await self._event_store.async_load()
        if cached_events:
            self._islamic_events = [
                CalendarEvent(
                    summary=event["summary"],
                    start=datetime.fromisoformat(event["start"]) if isinstance(event["start"], str) else event["start"],
                    end=datetime.fromisoformat(event["end"]) if isinstance(event["end"], str) else event["end"],
                    description=event.get("description", "")
                )
                for event in cached_events
            ]
            _LOGGER.debug("Loaded cached Islamic events")

    async def save_events(self) -> None:
        """Save Islamic events to persistent storage."""
        events_data = [
            {
                "summary": e.summary,
                "start": e.start.isoformat(),
                "end": e.end.isoformat(),
                "description": e.description or ""
            }
            for e in self._islamic_events
        ]
        await self._event_store.async_save(events_data)
        _LOGGER.debug("Saved Islamic events")

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = dt.now(TIMEZONE)
        all_events = self._get_all_events(now, now.replace(year=now.year + 1))
        upcoming_events = [event for event in all_events if event.start >= now]
        return min(upcoming_events, key=lambda x: x.start) if upcoming_events else None

    def _get_all_events(self, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Get all events including both Islamic events and prayer times."""
        events = []
        events.extend(self._islamic_events)
        events.extend(self._prayer_times.get_events(start_date, end_date))
        return sorted(events, key=lambda x: x.start)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        return [
            event for event in self._get_all_events(start_date, end_date)
            if start_date <= event.start <= end_date
            or start_date <= event.end <= end_date
        ]

    async def async_update(self) -> None:
        """Update events and Hijri date, falling back to local data if API fetch fails."""
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch prayer times, but use cached data if it fails
                success = await self._prayer_times.fetch_prayer_times(session)
                if not success and not self._prayer_times._daily_prayer_times:
                    _LOGGER.warning("No prayer times available in cache or API, calendar may be incomplete")
                elif not success:
                    _LOGGER.info("Using cached prayer times data")

                # Always update attributes with whatever data we have
                current_prayer, next_prayer, next_prayer_time = self._prayer_times.get_current_and_next_prayer()
                prayer_times = self._prayer_times.get_prayer_times_utc()
                self._attr_extra_state_attributes.update({
                    "current": current_prayer or "Unknown",
                    "next": next_prayer or "Unknown",
                    **prayer_times,
                })

                today_date = dt.now(TIMEZONE).strftime("%d-%b-%Y")
                today_prayer_times = self._prayer_times._daily_prayer_times.get(today_date, {})
                hijri_date = today_prayer_times.get("hijri")

                if hijri_date:
                    hijri_year, hijri_month, hijri_day = hijri_date.split("-")
                    month_name = HIJRI_MONTHS.get(hijri_month, "Unknown")
                    hijri_full = f"{int(hijri_day):02d} {month_name} {hijri_year}"
                    self._attr_extra_state_attributes["hijri_date"] = hijri_date
                    self._attr_extra_state_attributes["hijri_full"] = hijri_full

                # Attempt to fetch Islamic events, but keep cached data if it fails
                async with session.get(ISLAMIC_EVENTS_API) as response:
                    if response.status != 200:
                        _LOGGER.warning("Failed to fetch Islamic events, HTTP %d: %s, using cached events", 
                                      response.status, await response.text())
                    else:
                        data = await response.json()
                        if data.get("status") != "OK!":
                            _LOGGER.warning("Invalid response from eSolat API: %s, using cached events", data)
                        else:
                            events = []
                            for event in data.get("event", []):
                                try:
                                    date_str = f"{event['tarikh_miladi']} 00:00:00"
                                    naive_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                                    start = naive_dt.replace(tzinfo=TIMEZONE)
                                    end = start.replace(hour=23, minute=59, second=59)
                                    events.append(
                                        CalendarEvent(
                                            summary=event["hari_peristiwa"].strip(),
                                            start=start,
                                            end=end,
                                            description=event.get("tarikh_desc", ""),
                                        )
                                    )
                                except (KeyError, ValueError) as err:
                                    _LOGGER.error("Error parsing event: %s", err)
                                    continue
                            self._islamic_events = events
                            await self.save_events()
                            _LOGGER.info("Successfully updated Islamic events from API")

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Network error during update, relying on cached data: %s", err)