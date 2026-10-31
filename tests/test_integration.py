"""eSolat Takwim v0.4: a year of timetable stored locally, JAKIM only when something is due."""
from datetime import timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.esolattakwim.coordinator import STORAGE_KEY

from .helpers import FakeJakim, advance, setup


async def test_setup_downloads_year_once_and_fills_entities(hass: HomeAssistant, aioclient_mock, frozen) -> None:
    jakim = FakeJakim(aioclient_mock)
    entry = await setup(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert jakim.calls == [("SGR01", "2026-01-01"), ("events", None)]

    fajr = hass.states.get("sensor.esolat_takwim_fajr")
    assert fajr.state == "2026-10-30T21:48:00+00:00"  # 05:48 MYT on 31 Oct
    assert fajr.attributes["time_24h"] == "05:48"
    assert fajr.attributes["time_12h"] == "05:48 AM"
    assert hass.states.get("sensor.esolat_takwim_isha").attributes["time_24h"] == "20:09"
    hijri = hass.states.get("sensor.esolat_takwim_hijri")
    assert hijri.state == "20 Jamadil Awwal 1448"
    assert hijri.attributes["date"] == "1448-05-20"

    cal = hass.states.get("calendar.esolat_takwim")
    assert cal.attributes["hijri_date"] == "1448-05-20"
    assert cal.attributes["hijri_full"] == "20 Jamadil Awwal 1448"
    assert cal.attributes["current"] == "Syuruk"
    assert cal.attributes["next"] == "Dhuhr"
    assert cal.attributes["dhuhr"] == "2026-10-31T05:00:00+00:00"
    assert cal.attributes["zone"] == "sgr01"
    assert cal.attributes["message"] == "Dhuhr"  # next event to start


async def test_no_api_calls_between_weekly_refreshes(hass: HomeAssistant, aioclient_mock, frozen) -> None:
    jakim = FakeJakim(aioclient_mock)
    await setup(hass)
    await advance(hass, frozen, timedelta(days=6, hours=23))
    assert jakim.count() == 2  # v0.3.5 would have made ~20,000 requests by now

    # Day rolled over locally: 1 Nov, still 20:09 Isyak, new Hijri day
    assert hass.states.get("sensor.esolat_takwim_hijri").attributes["date"] == "1448-05-27"

    await advance(hass, frozen, timedelta(hours=2))
    assert jakim.count("SGR01") == 2 and jakim.count("events") == 2  # weekly refresh


async def test_current_and_next_move_every_minute(hass: HomeAssistant, aioclient_mock, frozen) -> None:
    FakeJakim(aioclient_mock)
    await setup(hass)
    frozen.move_to("2026-10-31 20:30:00+08:00")
    await advance(hass, frozen, timedelta(minutes=1), timedelta(minutes=1))
    cal = hass.states.get("calendar.esolat_takwim")
    assert (cal.attributes["current"], cal.attributes["next"]) == ("Isha", "Imsak")
    frozen.move_to("2026-11-01 04:00:00+08:00")
    await advance(hass, frozen, timedelta(minutes=1), timedelta(minutes=1))
    cal = hass.states.get("calendar.esolat_takwim")
    assert (cal.attributes["current"], cal.attributes["next"]) == ("Isha", "Imsak")
    assert hass.states.get("sensor.esolat_takwim_hijri").state == "21 Jamadil Awwal 1448"


async def test_reload_and_restart_reuse_stored_year(hass: HomeAssistant, aioclient_mock, hass_storage, frozen) -> None:
    jakim = FakeJakim(aioclient_mock)
    entry = await setup(hass)
    saved = hass_storage[STORAGE_KEY]["data"]
    assert saved["zone"] == "sgr01" and len(saved["days"]) == 365 and list(saved["years"]) == ["2026"]

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert jakim.count() == 2
    assert hass.states.get("sensor.esolat_takwim_fajr").attributes["time_24h"] == "05:48"


async def test_jakim_down_with_stored_year_keeps_working(hass: HomeAssistant, aioclient_mock, frozen) -> None:
    jakim = FakeJakim(aioclient_mock)
    entry = await setup(hass)
    jakim.down = True
    await advance(hass, frozen, timedelta(days=8))
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.esolat_takwim_fajr").state != "unavailable"
    # Failed refreshes back off to every 6 hours instead of hammering JAKIM
    assert jakim.count("SGR01") <= 1 + 6


async def test_jakim_down_without_stored_year_retries_setup(hass: HomeAssistant, aioclient_mock, frozen) -> None:
    jakim = FakeJakim(aioclient_mock)
    jakim.down = True
    entry = await setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_december_prefetches_next_year_daily(hass: HomeAssistant, aioclient_mock, hass_storage, freezer) -> None:
    freezer.move_to("2026-12-10 10:00:00+08:00")
    jakim = FakeJakim(aioclient_mock)
    await setup(hass)
    assert ("SGR01", "2027-01-01") in jakim.calls
    # Not published yet: this year is still saved, and the retry waits a day
    assert list(hass_storage[STORAGE_KEY]["data"]["years"]) == ["2026"]
    await advance(hass, freezer, timedelta(hours=23))
    assert jakim.calls.count(("SGR01", "2027-01-01")) == 1

    jakim.published.add(2027)
    await advance(hass, freezer, timedelta(hours=2))
    assert jakim.calls.count(("SGR01", "2027-01-01")) == 2
    assert sorted(hass_storage[STORAGE_KEY]["data"]["years"]) == ["2026", "2027"]

    # New Year works even with JAKIM down, and 2026 is dropped
    jakim.down = True
    freezer.move_to("2027-01-01 00:30:00+08:00")
    await advance(hass, freezer, timedelta(hours=1))
    assert hass.states.get("sensor.esolat_takwim_fajr").state.startswith("2026-12-31T22:")
    assert list(hass_storage[STORAGE_KEY]["data"]["years"]) == ["2027"]
    assert not any(d.startswith("2026") for d in hass_storage[STORAGE_KEY]["data"]["days"])


async def test_calendar_events(hass: HomeAssistant, aioclient_mock, frozen, hass_client) -> None:
    FakeJakim(aioclient_mock)
    await setup(hass)
    client = await hass_client()
    resp = await client.get(
        "/api/calendars/calendar.esolat_takwim?start=2026-08-25T00:00:00%2B08:00&end=2026-08-26T00:00:00%2B08:00"
    )
    events = await resp.json()
    summaries = [e["summary"] for e in events]
    assert summaries[0] == "Maulidur Rasul"
    assert events[0]["start"] == {"date": "2026-08-25"} and events[0]["end"] == {"date": "2026-08-26"}
    assert summaries[1:] == ["Imsak", "Fajr", "Syuruk", "Dhuhr", "Asr", "Maghrib", "Isha"]
    assert "<" not in "".join(e.get("description") or "" for e in events)


async def test_zone_change_refetches_for_new_zone(hass: HomeAssistant, aioclient_mock, hass_storage, frozen) -> None:
    jakim = FakeJakim(aioclient_mock)
    entry = await setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"zone": "wly01"})
    await hass.async_block_till_done()
    assert entry.data["zone"] == "wly01"
    assert ("WLY01", "2026-01-01") in jakim.calls
    assert jakim.count("events") == 1  # national events kept across zones
    assert hass.states.get("calendar.esolat_takwim").attributes["zone"] == "wly01"
    assert hass_storage[STORAGE_KEY]["data"]["zone"] == "wly01"


async def test_remove_deletes_cache_and_legacy_files(hass: HomeAssistant, aioclient_mock, hass_storage, frozen) -> None:
    hass_storage["esolat_prayer_times"] = {"version": 1, "key": "esolat_prayer_times", "data": {"zone": "sgr01"}}
    hass_storage["esolat_events"] = {"version": 1, "key": "esolat_events", "data": []}
    FakeJakim(aioclient_mock)
    entry = await setup(hass)
    assert "esolat_prayer_times" not in hass_storage and "esolat_events" not in hass_storage
    assert STORAGE_KEY in hass_storage
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert STORAGE_KEY not in hass_storage


async def test_unreadable_cache_is_ignored(hass: HomeAssistant, aioclient_mock, hass_storage, frozen) -> None:
    hass_storage[STORAGE_KEY] = {"version": 1, "key": STORAGE_KEY, "data": {"zone": "sgr01", "years": {"x": 1}}}
    jakim = FakeJakim(aioclient_mock)
    await setup(hass)
    assert jakim.count("SGR01") == 1
    assert hass.states.get("sensor.esolat_takwim_fajr").attributes["time_24h"] == "05:48"


async def test_config_flow(hass: HomeAssistant, aioclient_mock, frozen) -> None:
    FakeJakim(aioclient_mock)
    from custom_components.esolattakwim.const import DOMAIN

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"zone": "sgr01"})
    assert result["type"] == "create_entry" and result["data"] == {"zone": "sgr01"}
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "abort"
