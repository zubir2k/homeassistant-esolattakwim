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
EVENTS_STORAGE_KEY = "esolat_events_{zone}"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the eSolat Takwim Malaysia Calendar platform."""
    zone = config_entry.data["zone"]
    calendar = EsolatCalendar(hass, zone)
    await calendar.load_cached_data()
    async_add_entities([calendar], True)

class EsolatCalendar(CalendarEntity):
    """eSolat calendar entity."""
    
    _attr_has_entity_name = True
    _attr_name = "eSolat Takwim"

    def __init__(self, hass: HomeAssistant, zone: str) -> None:
        """Initialize the calendar."""
        self.hass = hass
        self.zone = zone
        self._islamic_events: list[CalendarEvent] = []
        self._prayer_times = PrayerTimesData(zone, hass)
        self._attr_unique_id = f"esolat_takwim_{zone}"
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
        self._event_store = Store(hass, EVENTS_STORAGE_VERSION, EVENTS_STORAGE_KEY.format(zone=zone))

    async def load_cached_data(self) -> None:
        """Load cached Islamic events and prayer times."""
        await self._prayer_times.load_cached_data()
        cached_events = await self._event_store.async_load()
        if cached_events:
            self._islamic_events = [CalendarEvent(**event) for event in cached_events]
            _LOGGER.debug("Loaded cached Islamic events for zone %s", self.zone)

    async def save_events(self) -> None:
        """Save Islamic events to persistent storage."""
        events_data = [{"summary": e.summary, "start": e.start.isoformat(), "end": e.end.isoformat(), "description": e.description or ""}
                       for e in self._islamic_events]
        await self._event_store.async_save(events_data)
        _LOGGER.debug("Saved Islamic events for zone %s", self.zone)

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
        """Update events and Hijri date."""
        try:
            async with aiohttp.ClientSession() as session:
                # Update prayer times
                success = await self._prayer_times.fetch_prayer_times(session)
                if not success and not self._prayer_times._daily_prayer_times:
                    _LOGGER.warning("No prayer times available, using cached data if present")
                
                # Update prayer time attributes
                current_prayer, next_prayer, next_prayer_time = self._prayer_times.get_current_and_next_prayer()
                prayer_times = self._prayer_times.get_prayer_times_utc()

                self._attr_extra_state_attributes.update({
                    "current": current_prayer or "Unknown",
                    "next": next_prayer or "Unknown",
                    **prayer_times,
                })

                # Extract Hijri date
                today_date = dt.now(TIMEZONE).strftime("%d-%b-%Y")
                today_prayer_times = self._prayer_times._daily_prayer_times.get(today_date, {})
                hijri_date = today_prayer_times.get("hijri")

                if hijri_date:
                    hijri_year, hijri_month, hijri_day = hijri_date.split("-")
                    month_name = HIJRI_MONTHS.get(hijri_month, "Unknown")
                    hijri_full = f"{int(hijri_day):02d} {month_name} {hijri_year}"
                    self._attr_extra_state_attributes["hijri_date"] = hijri_date
                    self._attr_extra_state_attributes["hijri_full"] = hijri_full

                # Fetch Islamic calendar events
                async with session.get(ISLAMIC_EVENTS_API) as response:
                    if response.status != 200:
                        _LOGGER.warning("Failed to fetch Islamic events, using cached data: %s", response.status)
                        return

                    data = await response.json()
                    if data.get("status") != "OK!":
                        _LOGGER.warning("Invalid response from eSolat API, using cached data")
                        return

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

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error updating calendar, using cached data: %s", err)