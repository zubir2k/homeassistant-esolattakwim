"""Constants for the eSolat Takwim Malaysia integration."""
from zoneinfo import ZoneInfo
from homeassistant.helpers.device_registry import DeviceEntryType

from esolat import (
    API_ENDPOINTS,
    HIJRI_MONTHS as HIJRI_MONTHS,
    ZONES as ESOLAT_ZONES,
)

DOMAIN = "esolattakwim"
VERSION = "0.4.4"
TIMEZONE = ZoneInfo("Asia/Kuala_Lumpur")

# API endpoints sourced from official esolat package
ISLAMIC_EVENTS_API = API_ENDPOINTS["jakim_events"]
PRAYER_TIMES_API = API_ENDPOINTS["jakim_takwim"] + "{zone}"

# Prayer names mapping
PRAYER_NAMES = {
    "imsak": "Imsak",
    "fajr": "Fajr",
    "syuruk": "Syuruk",
    "dhuhr": "Dhuhr",
    "asr": "Asr",
    "maghrib": "Maghrib",
    "isha": "Isha"
}

# Zone codes and names (extended with legacy/special district codes)
ZONES = {
    **ESOLAT_ZONES,
    "phg07": "PHG07 - Zon Khas Daerah Rompin, (Mukim Rompin, Mukim Endau, Mukim Pontian)",
}

def get_device_info(entry_id: str, zone: str | None = None) -> dict:
    """Return shared device info for all eSolat entities."""
    if zone is None:
        zone = entry_id
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "eSolat Takwim Malaysia",
        "manufacturer": "JAKIM / e-Solat",
        "model": f"Prayer Times Service ({zone.upper()})",
        "entry_type": DeviceEntryType.SERVICE,
        "configuration_url": "https://www.e-solat.gov.my/",
        "sw_version": VERSION,
    }
