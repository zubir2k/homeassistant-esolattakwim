"""Prayer times data handling for eSolat Takwim Malaysia."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Dict, Optional, Tuple

import aiohttp

from homeassistant.components.calendar import CalendarEvent
from homeassistant.util import dt

from .const import PRAYER_NAMES, PRAYER_TIMES_API, TIMEZONE
from .utils import format_prayer_times, get_next_prayer_info

_LOGGER = logging.getLogger(__name__)

class PrayerTimesData:
    """Class to handle prayer times data."""

    def __init__(self, zone: str) -> None:
        """Initialize the prayer times data."""
        self._prayer_times: dict[str, list[CalendarEvent]] = {}
        self._last_update_year: int | None = None
        self._daily_prayer_times: Dict[str, Dict[str, str]] = {}
        self._zone = zone

    def get_todays_prayer_times(self) -> dict[str, str]:
        """Get prayer times for today."""
        today = dt.now(TIMEZONE).strftime("%d-%b-%Y")
        prayer_times = self._daily_prayer_times.get(today, {})
        return format_prayer_times(prayer_times)

    def get_next_prayer(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the next prayer name and time."""
        prayer_times = self.get_todays_prayer_times()
        return get_next_prayer_info(prayer_times)

    async def fetch_prayer_times(self, session: aiohttp.ClientSession) -> bool:
        """Fetch prayer times for the current year."""
        current_year = dt.now(TIMEZONE).year

        # Only update if we haven't fetched this year's data yet
        if self._last_update_year == current_year:
            return True

        try:
            url = PRAYER_TIMES_API.format(zone=self._zone)
            async with session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to get prayer times from eSolat API")
                    return False

                data = await response.json()
                if data.get("status") != "OK!":
                    _LOGGER.error("Invalid response from eSolat Prayer Times API")
                    return False

                self._prayer_times = {}
                self._daily_prayer_times = {}
                
                for prayer_time in data.get("prayerTime", []):
                    try:
                        date_str = prayer_time["date"]
                        date = datetime.strptime(date_str, "%d-%b-%Y").replace(tzinfo=TIMEZONE)

                        # Store daily prayer times
                        prayer_dict = {}
                        for prayer in PRAYER_NAMES:
                            if prayer in prayer_time:
                                prayer_dict[prayer] = prayer_time[prayer]
                        self._daily_prayer_times[date_str] = prayer_dict

                        # Create calendar events for each prayer time
                        for prayer, display_name in PRAYER_NAMES.items():
                            if prayer in prayer_time:
                                try:
                                    time_str = prayer_time[prayer]
                                    time_parts = time_str.split(":")
                                    if len(time_parts) >= 2:
                                        hour = int(time_parts[0])
                                        minute = int(time_parts[1])
                                        
                                        # Ensure valid hour and minute values
                                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                                            start = date.replace(hour=hour, minute=minute)
                                            # Prayer events last for 15 minutes, but ensure we don't overflow
                                            end_minute = (minute + 15) % 60
                                            end_hour = hour + ((minute + 15) // 60)
                                            if end_hour > 23:
                                                end_hour = 23
                                                end_minute = 59
                                            
                                            end = date.replace(hour=end_hour, minute=end_minute)
                                            
                                            event = CalendarEvent(
                                                summary=f"{display_name} Prayer",
                                                start=start,
                                                end=end,
                                            )
                                            
                                            if prayer not in self._prayer_times:
                                                self._prayer_times[prayer] = []
                                            self._prayer_times[prayer].append(event)
                                except (ValueError, IndexError) as err:
                                    _LOGGER.error("Error parsing time %s: %s", time_str, err)
                                    continue
                                
                    except (KeyError, ValueError) as err:
                        _LOGGER.error("Error parsing prayer time: %s", err)
                        continue

                self._last_update_year = current_year
                return True

        except (aiohttp.ClientError, Exception) as err:
            _LOGGER.error("Error fetching prayer times: %s", err)
            return False

    def get_events(self, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Get prayer time events within the specified date range."""
        events = []
        for prayer_events in self._prayer_times.values():
            events.extend([
                event for event in prayer_events
                if start_date <= event.start <= end_date
                or start_date <= event.end <= end_date
            ])
        return sorted(events, key=lambda x: x.start)