"""Diagnostics support for eSolat Takwim Malaysia."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import TIMEZONE
from .coordinator import TakwimConfigEntry

TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TakwimConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    now = dt_util.now(TIMEZONE)
    today = now.date()

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "zone": coordinator.zone,
            "years": {str(y): dt.isoformat() for y, dt in coordinator.years.items()},
            "days_count": len(coordinator.days),
            "events_count": len(coordinator.events),
            "events_fetched": coordinator.events_fetched.isoformat() if coordinator.events_fetched else None,
            "today_date": today.isoformat(),
            "today_prayer_times": coordinator.day(today),
        },
    }
