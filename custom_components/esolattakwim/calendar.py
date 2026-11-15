"""Calendar for eSolat Takwim Malaysia: daily prayers plus JAKIM's Islamic events."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import PRAYER_NAMES, TIMEZONE
from .coordinator import TakwimConfigEntry, TakwimCoordinator
from .entity import TakwimEntity
from .sensor import hijri_text

PARALLEL_UPDATES = 0
PRAYER_EVENT_LENGTH = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant, entry: TakwimConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([EsolatCalendar(entry.runtime_data)])


def _start(event: CalendarEvent) -> datetime:
    """Comparable start for timed and all-day events."""
    start = event.start
    if isinstance(start, datetime):
        return start
    return datetime(start.year, start.month, start.day, tzinfo=TIMEZONE)


def _end(event: CalendarEvent) -> datetime:
    end = event.end
    if isinstance(end, datetime):
        return end
    return datetime(end.year, end.month, end.day, tzinfo=TIMEZONE)


class EsolatCalendar(TakwimEntity, CalendarEntity):
    """calendar.esolat_takwim"""

    _attr_name = None
    _attr_unique_id = "esolat_takwim"

    def __init__(self, coordinator: TakwimCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_id = "calendar.esolat_takwim"

    async def async_added_to_hass(self) -> None:
        """Current/next prayer move on every minute; that is local maths, not an API call."""
        await super().async_added_to_hass()

        @callback
        def _tick(_now: datetime) -> None:
            self.async_write_ha_state()

        self.async_on_remove(async_track_time_change(self.hass, _tick, second=0))

    # ---------------------------------------------------------------- events

    def _prayer_events(self, first: date, last: date) -> list[CalendarEvent]:
        events = []
        day = first
        while day <= last:
            for prayer, at in self.coordinator.prayer_times(day).items():
                events.append(CalendarEvent(summary=PRAYER_NAMES[prayer], start=at, end=at + PRAYER_EVENT_LENGTH))
            day += timedelta(days=1)
        return events

    def _islamic_events(self, first: date, last: date) -> list[CalendarEvent]:
        events = []
        for raw in self.coordinator.events:
            day = date.fromisoformat(raw["date"])
            if first <= day <= last:
                events.append(
                    CalendarEvent(
                        summary=raw["summary"],
                        start=day,
                        end=day + timedelta(days=1),
                        description=raw.get("description") or None,
                    )
                )
        return events

    def _events_between(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        first = start.astimezone(TIMEZONE).date() - timedelta(days=1)
        last = end.astimezone(TIMEZONE).date()
        events = self._islamic_events(first, last) + self._prayer_events(first, last)
        return sorted((e for e in events if _start(e) < end and _end(e) > start), key=_start)

    @property
    def event(self) -> CalendarEvent | None:
        """The next event to start (a prayer, or an Islamic event if one falls first)."""
        now = dt_util.now(TIMEZONE)
        upcoming = [e for e in self._events_between(now, now + timedelta(days=2)) if _start(e) >= now]
        if upcoming:
            return upcoming[0]
        later = [e for e in self._islamic_events(now.date(), now.date() + timedelta(days=366)) if _start(e) >= now]
        return later[0] if later else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return self._events_between(start_date, end_date)

    # ------------------------------------------------------------ attributes

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        now = dt_util.now(TIMEZONE)
        today = now.date()
        raw_hijri = self.coordinator.day(today).get("hijri") or None
        current, nxt, _ = self.coordinator.current_and_next(now)
        attrs: dict[str, Any] = {
            "hijri_date": raw_hijri,
            "hijri_full": hijri_text(raw_hijri),
            "current": current or "Unknown",
            "next": nxt or "Unknown",
        }
        times = self.coordinator.prayer_times(today)
        for prayer in PRAYER_NAMES:
            at = times.get(prayer)
            attrs[prayer] = dt_util.as_utc(at).strftime("%Y-%m-%dT%H:%M:%S+00:00") if at else None
        attrs["zone"] = self.coordinator.zone
        return attrs
