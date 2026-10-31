"""Keeps a year of JAKIM prayer times for one zone, so day-to-day use needs no API at all.

JAKIM is contacted only when:
  * this year's timetable is missing (first install, zone change, new year without a prefetch);
  * the stored year is a week old (JAKIM occasionally revises a timetable);
  * it is December and next year is not stored yet (tried once a day until JAKIM publishes it);
  * the Islamic events list is a week old.
Everything else (today's times, current/next prayer, calendar events) is computed locally.
"""
from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, ISLAMIC_EVENTS_API, PRAYER_NAMES, PRAYER_TIMES_API, TIMEZONE

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.cache"
LEGACY_STORAGE_KEYS = ("esolat_prayer_times", "esolat_events")

UPDATE_INTERVAL = timedelta(hours=1)  # a local check; JAKIM is only called when something is due
REFRESH_AFTER = timedelta(days=7)  # re-download the stored year / events this often
RETRY_AFTER = timedelta(hours=6)  # when a refresh fails but stored data is still usable
NEXT_YEAR_RETRY = timedelta(days=1)  # December: next year is usually published late
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

ROW_FIELDS = (*PRAYER_NAMES, "dhuha")

type TakwimConfigEntry = ConfigEntry["TakwimCoordinator"]


def cache_store(hass: HomeAssistant, key: str = STORAGE_KEY) -> Store:
    return Store(hass, STORAGE_VERSION, key)


def _clean_html(text: str | None) -> str:
    """JAKIM event descriptions are HTML fragments; calendars want plain text."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


class TakwimCoordinator(DataUpdateCoordinator[dict]):
    """Data is {"YYYY-MM-DD": {"hijri": "1448-05-20", "fajr": "06:01:00", ...}} for every stored day."""

    config_entry: TakwimConfigEntry

    def __init__(self, hass: HomeAssistant, entry: TakwimConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="eSolat Takwim",
            update_interval=UPDATE_INTERVAL,
        )
        self.zone: str = entry.data["zone"].lower()
        self.days: dict[str, dict[str, str]] = {}
        self.years: dict[int, datetime] = {}  # year -> when it was downloaded
        self.events: list[dict[str, str]] = []  # {"date": "2026-03-20", "summary": ..., "description": ...}
        self.events_fetched: datetime | None = None
        self._tried: dict[str, datetime] = {}  # last attempt per download, so failures back off
        self._store = cache_store(hass)
        self._loaded = False
        self._dirty = False

    # ----------------------------------------------------------------- storage

    async def _async_load(self) -> None:
        self._loaded = True
        try:
            stored = await self._store.async_load() or {}
            if stored.get("zone") == self.zone:
                self.days = dict(stored.get("days") or {})
                self.years = {int(y): datetime.fromisoformat(t) for y, t in (stored.get("years") or {}).items()}
            elif stored:
                _LOGGER.info("Zone changed to %s; the stored timetable is for %s", self.zone.upper(), stored.get("zone"))
                self._dirty = True
            # Islamic events are national, so they survive a zone change
            self.events = list(stored.get("events") or [])
            if stored.get("events_fetched"):
                self.events_fetched = datetime.fromisoformat(stored["events_fetched"])
        except Exception as err:  # noqa: BLE001 - a bad cache must never block setup
            _LOGGER.warning("Ignoring unreadable eSolat Takwim cache: %s", err)
            self.days, self.years, self.events, self.events_fetched = {}, {}, [], None

    async def _async_save(self) -> None:
        self._dirty = False
        await self._store.async_save(
            {
                "zone": self.zone,
                "years": {str(y): t.isoformat() for y, t in self.years.items()},
                "days": self.days,
                "events": self.events,
                "events_fetched": self.events_fetched.isoformat() if self.events_fetched else None,
            }
        )

    # ------------------------------------------------------------------ update

    def _due(self, key: str, fetched: datetime | None, now: datetime, every: timedelta, retry: timedelta) -> bool:
        if fetched is not None and now - fetched < every:
            return False
        tried = self._tried.get(key)
        return tried is None or now - tried >= retry

    async def _async_update_data(self) -> dict:
        if not self._loaded:
            await self._async_load()

        now = dt_util.now(TIMEZONE)
        year = now.year
        self._drop_years_before(year)
        session = async_get_clientsession(self.hass)

        # This year: needed now. Retried every update while missing, every 6 h once stored.
        have = self.years.get(year)
        if self._due(f"year{year}", have, now, REFRESH_AFTER, UPDATE_INTERVAL if have is None else RETRY_AFTER):
            await self._async_fetch_year(session, year, now)

        # Next year: prefetched in December so 1 January needs no API.
        nxt = self.years.get(year + 1)
        if now.month == 12 and self._due(f"year{year + 1}", nxt, now, REFRESH_AFTER, NEXT_YEAR_RETRY):
            await self._async_fetch_year(session, year + 1, now)

        if self._due("events", self.events_fetched, now, REFRESH_AFTER, RETRY_AFTER):
            await self._async_fetch_events(session, now)

        if self._dirty:
            await self._async_save()

        if now.date().isoformat() not in self.days:
            raise UpdateFailed(f"No prayer times stored for {now.date()} and JAKIM could not be reached")
        return self.days

    def _drop_years_before(self, year: int) -> None:
        old = [d for d in self.days if d[:4].isdigit() and int(d[:4]) < year]
        for d in old:
            del self.days[d]
        for y in [y for y in self.years if y < year]:
            del self.years[y]
        if old:
            self._dirty = True

    async def _async_fetch_year(self, session: aiohttp.ClientSession, year: int, now: datetime) -> bool:
        """Download one calendar year. On any failure the stored copy (if any) is kept."""
        self._tried[f"year{year}"] = now
        form = {"datestart": f"{year}-01-01", "dateend": f"{year}-12-31"}
        try:
            async with session.post(
                PRAYER_TIMES_API.format(zone=self.zone.upper()), data=form, timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("JAKIM returned HTTP %s for %s %s", resp.status, self.zone.upper(), year)
                    return False
                payload = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning("Could not fetch %s prayer times for %s: %s", year, self.zone.upper(), err)
            return False

        if not isinstance(payload, dict):
            _LOGGER.warning("Unexpected JAKIM response for %s %s", self.zone.upper(), year)
            return False
        rows = payload.get("prayerTime")
        if payload.get("status") == "NO_RECORD!" and year > now.year:
            _LOGGER.debug("JAKIM has not published %s yet", year)
            return False
        if payload.get("status") != "OK!" or not isinstance(rows, list) or not rows:
            _LOGGER.warning("Unexpected JAKIM response for %s %s: %s", self.zone.upper(), year, payload.get("status"))
            return False

        # JAKIM localises month names ("31-Dis-2026"), so days are keyed by position from 1 January.
        start = date(year, 1, 1)
        days: dict[str, dict[str, str]] = {}
        for idx, row in enumerate(rows):
            day = start + timedelta(days=idx)
            if day.year != year:
                break
            entry = {"hijri": row.get("hijri", "")}
            entry.update({f: row[f] for f in ROW_FIELDS if row.get(f)})
            days[day.isoformat()] = entry

        for d in [d for d in self.days if d.startswith(f"{year}-")]:
            del self.days[d]
        self.days.update(days)
        self.years[year] = now
        self._dirty = True
        _LOGGER.info("Stored %d days of %s prayer times for %s", len(days), year, self.zone.upper())
        return True

    async def _async_fetch_events(self, session: aiohttp.ClientSession, now: datetime) -> bool:
        self._tried["events"] = now
        try:
            async with session.get(ISLAMIC_EVENTS_API, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    _LOGGER.warning("JAKIM returned HTTP %s for Islamic events", resp.status)
                    return False
                payload = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning("Could not fetch Islamic events: %s", err)
            return False

        if not isinstance(payload, dict) or payload.get("status") != "OK!":
            _LOGGER.warning("Unexpected JAKIM Islamic events response")
            return False

        events = []
        for raw in payload.get("event") or []:
            try:
                day = date.fromisoformat(raw["tarikh_miladi"])
                summary = raw["hari_peristiwa"].strip()
            except (KeyError, TypeError, ValueError):
                continue
            events.append(
                {"date": day.isoformat(), "summary": summary, "description": _clean_html(raw.get("tarikh_desc"))}
            )
        self.events = sorted(events, key=lambda e: e["date"])
        self.events_fetched = now
        self._dirty = True
        return True

    # ------------------------------------------------------------ local queries

    def day(self, when: date) -> dict[str, str]:
        return (self.data or self.days).get(when.isoformat(), {})

    def prayer_times(self, when: date) -> dict[str, datetime]:
        """The seven prayers of one day as local datetimes, in order."""
        row = self.day(when)
        times = {}
        for prayer in PRAYER_NAMES:
            value = row.get(prayer)
            if not value:
                continue
            try:
                hour, minute = (int(p) for p in value.split(":")[:2])
            except ValueError:
                continue
            times[prayer] = datetime(when.year, when.month, when.day, hour, minute, tzinfo=TIMEZONE)
        return dict(sorted(times.items(), key=lambda kv: kv[1]))

    def current_and_next(self, now: datetime) -> tuple[str | None, str | None, datetime | None]:
        """(current prayer, next prayer, next prayer time), crossing midnight when needed."""
        today = now.astimezone(TIMEZONE).date()
        timeline = [
            (prayer, at)
            for day in (today - timedelta(days=1), today, today + timedelta(days=1))
            for prayer, at in self.prayer_times(day).items()
        ]
        current = nxt = None
        for prayer, at in timeline:
            if at <= now:
                current = (prayer, at)
            else:
                nxt = (prayer, at)
                break
        return (
            PRAYER_NAMES[current[0]] if current else None,
            PRAYER_NAMES[nxt[0]] if nxt else None,
            nxt[1] if nxt else None,
        )
