"""A fake JAKIM: counts requests and serves the saved 2026 SGR01 year."""
from __future__ import annotations

import copy
from datetime import timedelta

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.esolattakwim.const import DOMAIN, ISLAMIC_EVENTS_API, PRAYER_TIMES_API

from .conftest import load_json

YEAR_2026 = load_json("takwim_sgr01_2026.json")
NO_RECORD = load_json("takwim_no_record.json")
EVENTS = load_json("islamic_events.json")


def year_payload(year: int) -> dict:
    """2026's rows reused for another year (only the row count matters to the parser)."""
    if year == 2026:
        return YEAR_2026
    data = copy.deepcopy(YEAR_2026)
    rows = data["prayerTime"]
    days = 366 if year % 4 == 0 else 365
    data["prayerTime"] = (rows + rows[-1:])[:days]
    return data


class FakeJakim:
    def __init__(self, aioclient_mock) -> None:
        self.calls: list[tuple[str, str | None]] = []  # (zone, datestart) or ("events", None)
        self.published = {2026}
        self.down = False
        self._mock = aioclient_mock
        for zone in ("SGR01", "WLY01"):
            aioclient_mock.post(PRAYER_TIMES_API.format(zone=zone), side_effect=self._takwim)
        aioclient_mock.get(ISLAMIC_EVENTS_API, side_effect=self._events)

    async def _takwim(self, method, url, data):
        zone = url.query.get("zone")
        start = data["datestart"]
        self.calls.append((zone, start))
        if self.down:
            return AiohttpClientMockResponse(method, url, status=500, text="oops")
        year = int(start[:4])
        payload = year_payload(year) if year in self.published else NO_RECORD
        return AiohttpClientMockResponse(method, url, json=payload)

    async def _events(self, method, url, data):
        self.calls.append(("events", None))
        if self.down:
            return AiohttpClientMockResponse(method, url, status=500, text="oops")
        return AiohttpClientMockResponse(method, url, json=EVENTS)

    def count(self, what: str | None = None) -> int:
        return sum(1 for c in self.calls if what is None or c[0] == what)


async def setup(hass, zone: str = "sgr01") -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title="eSolat Takwim Malaysia", data={"zone": zone})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def advance(hass, freezer, delta: timedelta, step: timedelta = timedelta(hours=1)) -> None:
    """Walk the clock forward so every hourly update and midnight tick fires."""
    remaining = delta
    while remaining > timedelta(0):
        jump = min(step, remaining)
        freezer.tick(jump)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        remaining -= jump
