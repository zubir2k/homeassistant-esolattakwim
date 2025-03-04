"""Prayer times data handling for eSolat Takwim Malaysia."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Tuple
import aiohttp
from aiohttp import FormData

from homeassistant.components.calendar import CalendarEvent
from homeassistant.util import dt
from homeassistant.helpers.storage import Store

from .const import PRAYER_NAMES, PRAYER_TIMES_API, TIMEZONE
from .utils import format_prayer_times, get_next_prayer_info

_LOGGER = logging.getLogger(__name__)

class PrayerTimesData:
    """Class to handle prayer times data."""

    STORAGE_VERSION = 1
    STORAGE_KEY = "esolat_prayer_times"  # Static key

    def __init__(self, zone: str, hass) -> None:
        """Initialize the prayer times data with Home Assistant instance."""
        self._prayer_times: dict[str, list[CalendarEvent]] = {}
        self._last_update_year: int | None = None
        self._daily_prayer_times: Dict[str, Dict[str, str]] = {}
        self._zone = zone
        self.hass = hass
        self._store = Store(hass, self.STORAGE_VERSION, self.STORAGE_KEY)

    async def load_cached_data(self) -> None:
        """Load cached prayer times from storage, checking zone consistency."""
        cached_data = await self._store.async_load()
        if cached_data:
            cached_zone = cached_data.get("zone")
            if cached_zone != self._zone:
                _LOGGER.warning("Cached prayer times zone (%s) does not match current zone (%s), clearing cache", cached_zone, self._zone)
                self._daily_prayer_times = {}
                self._prayer_times = {}
                self._last_update_year = None
            else:
                self._daily_prayer_times = cached_data.get("daily_prayer_times", {})
                self._last_update_year = cached_data.get("last_update_year")
                prayer_times_raw = cached_data.get("prayer_times", {})
                self._prayer_times = {
                    prayer: [CalendarEvent(**event) for event in events]
                    for prayer, events in prayer_times_raw.items()
                }
                _LOGGER.debug("Loaded cached prayer times for zone %s", self._zone)
        else:
            _LOGGER.debug("No cached prayer times found")

    async def save_data(self) -> None:
        """Save prayer times to persistent storage with zone code."""
        data = {
            "zone": self._zone,  # Add zone code to JSON
            "daily_prayer_times": self._daily_prayer_times,
            "prayer_times": {
                prayer: [{"summary": e.summary, "start": e.start.isoformat(), "end": e.end.isoformat()}
                         for e in events]
                for prayer, events in self._prayer_times.items()
            },
            "last_update_year": self._last_update_year
        }
        await self._store.async_save(data)
        _LOGGER.debug("Saved prayer times for zone %s", self._zone)

    def get_todays_prayer_times(self) -> dict[str, str]:
        """Get prayer times for today."""
        today = dt.now(TIMEZONE).strftime("%d-%b-%Y")
        prayer_times = self._daily_prayer_times.get(today, {})
        return format_prayer_times(prayer_times)

    def get_next_prayer(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the next prayer name and time."""
        prayer_times = self.get_todays_prayer_times()
        return get_next_prayer_info(prayer_times)

    def get_prayer_times_utc(self) -> dict[str, str]:
        """Get prayer times for today in UTC format."""
        today = dt.now(TIMEZONE).strftime("%d-%b-%Y")
        local_prayer_times = self._daily_prayer_times.get(today, {})
        utc_prayer_times = {}
        
        today_date = dt.now(TIMEZONE).date()
        
        for prayer, time_str in local_prayer_times.items():
            try:
                time_parts = time_str.split(":")
                if len(time_parts) >= 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = int(time_parts[2]) if len(time_parts) > 2 else 0
                    
                    local_dt = datetime.combine(
                        today_date,
                        datetime.strptime(f"{hour:02d}:{minute:02d}:{second:02d}", "%H:%M:%S").time()
                    ).replace(tzinfo=TIMEZONE)
                    
                    utc_dt = local_dt.astimezone(dt.UTC)
                    utc_prayer_times[prayer] = utc_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            except (ValueError, IndexError):
                utc_prayer_times[prayer] = None
                
        return utc_prayer_times

    def get_current_and_next_prayer(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Get the current and next prayer name and time."""
        prayer_times = self.get_todays_prayer_times()
        if not prayer_times:
            return None, None, None

        now = dt.now(TIMEZONE)
        current_time = now.time()

        current_prayer = None
        next_prayer = None
        next_prayer_time = None

        def normalize_time(time_str: str) -> str:
            """Ensure time is in %H:%M:%S format by adding seconds if missing."""
            if len(time_str.split(":")) == 2:
                return f"{time_str}:00"
            return time_str

        normalized_prayers = {
            prayer: normalize_time(time_str) for prayer, time_str in prayer_times.items()
        }

        sorted_prayers = sorted(
            [(k, v) for k, v in normalized_prayers.items() if ":" in v],
            key=lambda x: datetime.strptime(x[1], "%H:%M:%S"),
        )

        for i, (prayer, time_str) in enumerate(sorted_prayers):
            prayer_time = datetime.strptime(time_str, "%H:%M:%S").time()
            if prayer_time > current_time:
                next_prayer = PRAYER_NAMES.get(prayer, prayer)
                next_prayer_time = time_str
                if i > 0:
                    current_prayer = PRAYER_NAMES.get(sorted_prayers[i - 1][0], sorted_prayers[i - 1][0])
                break

        if not next_prayer and sorted_prayers:
            current_prayer = PRAYER_NAMES.get(sorted_prayers[-1][0], sorted_prayers[-1][0])
            next_day = (now + timedelta(days=1)).strftime("%d-%b-%Y")
            next_day_prayer_times = self._daily_prayer_times.get(next_day, {})
            if next_day_prayer_times:
                sorted_next_day_prayers = sorted(
                    [(k, v) for k, v in next_day_prayer_times.items() if ":" in v],
                    key=lambda x: datetime.strptime(normalize_time(x[1]), "%H:%M:%S"),
                )
                if sorted_next_day_prayers:
                    next_prayer = PRAYER_NAMES.get(sorted_next_day_prayers[0][0], sorted_next_day_prayers[0][0])
                    next_prayer_time = normalize_time(sorted_next_day_prayers[0][1])

        if not current_prayer:
            previous_day = (now - timedelta(days=1)).strftime("%d-%b-%Y")
            previous_prayer_times = self._daily_prayer_times.get(previous_day, {})
            if previous_prayer_times:
                sorted_previous_prayers = sorted(
                    [(k, v) for k, v in previous_prayer_times.items() if ":" in v],
                    key=lambda x: datetime.strptime(normalize_time(x[1]), "%H:%M:%S"),
                )
                if sorted_previous_prayers:
                    current_prayer = PRAYER_NAMES.get(sorted_previous_prayers[-1][0], sorted_previous_prayers[-1][0])

        return current_prayer, next_prayer, next_prayer_time

    async def fetch_prayer_times(self, session: aiohttp.ClientSession) -> bool:
        """Fetch prayer times for the current year and store Hijri dates."""
        current_year = dt.now(TIMEZONE).year
        current_month = dt.now(TIMEZONE).month

        self._prayer_times.clear()

        self._purge_old_prayer_times(current_year)

        async def _fetch_yearly_prayer_times(year: int):
            url = PRAYER_TIMES_API.format(zone=self._zone)
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)

            form_data = FormData()
            form_data.add_field('datestart', start_date.strftime('%Y-%m-%d'))
            form_data.add_field('dateend', end_date.strftime('%Y-%m-%d'))

            async with session.post(url, data=form_data) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch prayer times for year %d", year)
                    return False

                data = await response.json()
                if data.get("status") != "OK!":
                    _LOGGER.error("Invalid response from eSolat Prayer Times API for year %d", year)
                    return False

                for prayer_time in data.get("prayerTime", []):
                    try:
                        date_str = prayer_time["date"]
                        hijri_date = prayer_time["hijri"]
                        self._daily_prayer_times[date_str] = {
                            "hijri": hijri_date,
                            **{prayer: prayer_time[prayer] for prayer in PRAYER_NAMES if prayer in prayer_time},
                        }
                        for prayer, display_name in PRAYER_NAMES.items():
                            if prayer in prayer_time:
                                time_str = prayer_time[prayer]
                                time_parts = time_str.split(":")
                                if len(time_parts) >= 2:
                                    hour = int(time_parts[0])
                                    minute = int(time_parts[1])
                                    date = datetime.strptime(date_str, "%d-%b-%Y").replace(tzinfo=TIMEZONE)
                                    start = date.replace(hour=hour, minute=minute)
                                    end_minute = (minute + 15) % 60
                                    end_hour = hour + ((minute + 15) // 60)
                                    end = date.replace(hour=end_hour, minute=end_minute)

                                    event = CalendarEvent(
                                        summary=f"{display_name}",
                                        start=start,
                                        end=end,
                                    )
                                    if prayer not in self._prayer_times:
                                        self._prayer_times[prayer] = []
                                    self._prayer_times[prayer].append(event)
                    except (KeyError, ValueError) as err:
                        _LOGGER.error("Error parsing prayer time: %s", err)
                        continue
            return True

        success = await _fetch_yearly_prayer_times(current_year)
        if current_month == 12:
            success &= await _fetch_yearly_prayer_times(current_year + 1)

        if success:
            self._last_update_year = current_year
            await self.save_data()

        return success

    def _purge_old_prayer_times(self, current_year: int) -> None:
        """Purge all prayer times before the current year."""
        keys_to_delete = [
            date_str for date_str in self._daily_prayer_times.keys()
            if datetime.strptime(date_str, "%d-%b-%Y").year < current_year
        ]
        for key in keys_to_delete:
            del self._daily_prayer_times[key]

        for prayer in list(self._prayer_times.keys()):
            self._prayer_times[prayer] = [
                event for event in self._prayer_times[prayer]
                if event.start.year >= current_year
            ]
            if not self._prayer_times[prayer]:
                del self._prayer_times[prayer]

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
