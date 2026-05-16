"""The eSolat Takwim Malaysia integration."""
from __future__ import annotations

from datetime import datetime
import aiofiles.os
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, PRAYER_NAMES, TIMEZONE

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

PRAYER_TIMES_STORAGE_VERSION = 1
PRAYER_TIMES_STORAGE_KEY = "esolat_prayer_times"
PRAYER_TIMES_DATA_VERSION = 2

_MONTH_ALIASES = {
    "jan": "Jan",
    "feb": "Feb",
    "mar": "Mar",
    "mac": "Mar",
    "apr": "Apr",
    "may": "May",
    "mei": "May",
    "jun": "Jun",
    "jul": "Jul",
    "aug": "Aug",
    "ogo": "Aug",
    "ogos": "Aug",
    "sep": "Sep",
    "oct": "Oct",
    "okt": "Oct",
    "nov": "Nov",
    "dec": "Dec",
    "dis": "Dec",
}


def _parse_any_storage_date(date_str: str) -> datetime | None:
    """Parse both canonical English and legacy Malay month storage keys."""
    try:
        return datetime.strptime(date_str, "%d-%b-%Y")
    except ValueError:
        pass

    parts = date_str.split("-")
    if len(parts) != 3:
        return None

    day_str, month_str, year_str = parts
    month_norm = _MONTH_ALIASES.get(month_str.strip().lower())
    if month_norm is None:
        return None

    try:
        return datetime.strptime(
            f"{int(day_str):02d}-{month_norm}-{int(year_str):04d}",
            "%d-%b-%Y",
        )
    except ValueError:
        return None


def _canonical_storage_date(date_str: str) -> str | None:
    """Return canonical English %d-%b-%Y storage key."""
    parsed = _parse_any_storage_date(date_str)
    if parsed is None:
        return None
    return parsed.strftime("%d-%b-%Y")


def _payload_score(payload: dict) -> int:
    """Prefer richer payloads when duplicate day keys exist."""
    return sum(1 for value in payload.values() if value not in (None, "", "unknown"))


def _rebuild_prayer_events_from_daily(
    daily_prayer_times: dict[str, dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    """Rebuild prayer event cache from normalized daily prayer times."""
    prayer_events: dict[str, list[dict[str, str]]] = {}

    def _sort_key(item: str) -> datetime:
        parsed = _parse_any_storage_date(item)
        return parsed if parsed is not None else datetime.max

    for date_key in sorted(daily_prayer_times.keys(), key=_sort_key):
        parsed_date = _parse_any_storage_date(date_key)
        if parsed_date is None:
            _LOGGER.warning("Skipping invalid stored prayer date key during rebuild: %s", date_key)
            continue

        base_dt = parsed_date.replace(tzinfo=TIMEZONE)
        prayers = daily_prayer_times.get(date_key, {})

        for prayer, display_name in PRAYER_NAMES.items():
            time_str = prayers.get(prayer)
            if not time_str:
                continue

            try:
                parts = time_str.split(":")
                if len(parts) < 2:
                    continue

                hour = int(parts[0])
                minute = int(parts[1])

                start = base_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end = start.replace(
                    hour=(start.hour + ((start.minute + 15) // 60)) % 24,
                    minute=(start.minute + 15) % 60,
                )

                prayer_events.setdefault(prayer, []).append(
                    {
                        "summary": display_name,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                    }
                )
            except (ValueError, IndexError):
                _LOGGER.warning(
                    "Skipping invalid %s time '%s' for stored date %s",
                    prayer,
                    time_str,
                    date_key,
                )

    return prayer_events


async def _migrate_prayer_times_storage(hass: HomeAssistant) -> None:
    """Normalize legacy stored prayer dates and rebuild prayer event cache once."""
    store = Store(hass, PRAYER_TIMES_STORAGE_VERSION, PRAYER_TIMES_STORAGE_KEY)
    cached_data = await store.async_load()

    if not cached_data:
        return

    current_data_version = cached_data.get("data_version", 1)
    daily_prayer_times = cached_data.get("daily_prayer_times", {})

    normalized_daily: dict[str, dict[str, str]] = {}
    changed = current_data_version < PRAYER_TIMES_DATA_VERSION

    for raw_key, payload in daily_prayer_times.items():
        canonical_key = _canonical_storage_date(raw_key)
        if canonical_key is None:
            changed = True
            _LOGGER.warning("Dropping invalid stored prayer date key: %s", raw_key)
            continue

        if canonical_key != raw_key:
            changed = True

        existing = normalized_daily.get(canonical_key)
        if existing is None:
            normalized_daily[canonical_key] = payload
            continue

        # Duplicate key after normalization; keep the richer payload
        changed = True
        if _payload_score(payload) > _payload_score(existing):
            normalized_daily[canonical_key] = payload

    rebuilt_events = _rebuild_prayer_events_from_daily(normalized_daily)
    if rebuilt_events != cached_data.get("prayer_times", {}):
        changed = True

    if not changed:
        return

    cached_data["daily_prayer_times"] = normalized_daily
    cached_data["prayer_times"] = rebuilt_events
    cached_data["data_version"] = PRAYER_TIMES_DATA_VERSION

    await store.async_save(cached_data)
    _LOGGER.info(
        "Migrated %s storage to normalized canonical prayer-date format (data_version=%s)",
        PRAYER_TIMES_STORAGE_KEY,
        PRAYER_TIMES_DATA_VERSION,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up eSolat Takwim Malaysia from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # One-time self-healing for existing mixed-language prayer date keys
    await _migrate_prayer_times_storage(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up storage files."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        prayer_times_file = hass.config.path("storage", "esolat_prayer_times.json")
        events_file = hass.config.path("storage", "esolat_events.json")

        for file_path in (prayer_times_file, events_file):
            if await aiofiles.os.path.exists(file_path):
                try:
                    await aiofiles.os.remove(file_path)
                    _LOGGER.debug("Removed storage file %s", file_path)
                except OSError as err:
                    _LOGGER.warning("Failed to remove storage file %s: %s", file_path, err)

        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
