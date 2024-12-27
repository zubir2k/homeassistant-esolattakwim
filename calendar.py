"""Support for eSolat Takwim Malaysia Calendar."""
from __future__ import annotations

import asyncio
from datetime import datetime
import logging
from typing import Any

import aiohttp

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt

from .const import DOMAIN, HIJRI_API, ISLAMIC_EVENTS_API, TIMEZONE, HIJRI_MONTHS, PRAYER_TIMES_API
from .prayer_times import PrayerTimesData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the eSolat Takwim Malaysia Calendar platform."""
    zone = config_entry.data["zone"]
    async_add_entities([EsolatCalendar(hass, zone)], True)

class EsolatCalendar(CalendarEntity):
    """eSolat calendar entity."""
    
    _attr_has_entity_name = True
    _attr_name = "eSolat Takwim"

    def __init__(self, hass: HomeAssistant, zone: str) -> None:
        """Initialize the calendar."""
        self.hass = hass
        self.zone = zone
        self._islamic_events: list[CalendarEvent] = []
        self._prayer_times = PrayerTimesData(zone)
        self._attr_unique_id = f"esolat_takwim_{zone}"
        self._attr_extra_state_attributes = {
            "hijri_date": None,
            "hijri_full": None,
            "next_prayer": None,
            "next_prayer_time": None,
            "todays_prayer_times": {},
            "zone": zone
        }

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

    async def _fetch_hijri_date(self, session: aiohttp.ClientSession) -> str | None:
        """Fetch current Hijri date."""
        try:
            current_date = dt.now(TIMEZONE).strftime("%Y-%m-%d")
            url = f"{HIJRI_API}&date={current_date}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to get Hijri date from eSolat API")
                    return None

                data = await response.json()
                if data.get("status") != "OK!":
                    _LOGGER.error("Invalid response from E-Solat Hijri API")
                    return None

                return data.get("takwim", {}).get(current_date)

        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError) as err:
            _LOGGER.error("Error fetching Hijri date: %s", err)
            return None

    async def async_update(self) -> None:
        """Update events and Hijri date."""
        try:
            async with aiohttp.ClientSession() as session:
                # Update prayer times
                await self._prayer_times.fetch_prayer_times(session)

                # Update prayer time attributes
                next_prayer_name, next_prayer_time = self._prayer_times.get_next_prayer()
                self._attr_extra_state_attributes.update({
                    "next_prayer": next_prayer_name or "Unknown",
                    "next_prayer_time": next_prayer_time or "Unknown",
                    "todays_prayer_times": self._prayer_times.get_todays_prayer_times() or {},
                })

                # Fetch Hijri date
                hijri_date = await self._fetch_hijri_date(session)
                if hijri_date:
                    try:
                        hijri_year, hijri_month, hijri_day = hijri_date.split("-")
                        month_name = HIJRI_MONTHS.get(hijri_month, "Unknown")
                        hijri_full = f"{int(hijri_day):02d} {month_name} {hijri_year}"
                        
                        self._attr_extra_state_attributes["hijri_date"] = hijri_date
                        self._attr_extra_state_attributes["hijri_full"] = hijri_full
                    except ValueError:
                        _LOGGER.error("Failed to parse Hijri date format")

                # Fetch Islamic calendar events
                async with session.get(ISLAMIC_EVENTS_API) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to get data from eSolat API")
                        return

                    data = await response.json()
                    if data.get("status") != "OK!":
                        _LOGGER.error("Invalid response from eSolat API")
                        return

                    events = []
                    current_year = dt.now(TIMEZONE).year
                    
                    for event in data.get("event", []):
                        try:
                            date_str = f"{event['tarikh_miladi']} 00:00:00"
                            naive_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                            
                            if naive_dt.year != current_year:
                                continue
                            
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

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error updating calendar: %s", err)