"""Utility functions for eSolat Takwim Malaysia."""
from datetime import datetime
from typing import Dict, Optional, Tuple

from homeassistant.util import dt

from .const import PRAYER_NAMES, TIMEZONE

def format_time(time_str: str) -> str:
    """Format time string to HH:MM format."""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
        return time_obj.strftime("%H:%M")
    except ValueError:
        return time_str

def get_next_prayer_info(prayer_times: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """Get the next prayer name and time."""
    if not prayer_times:
        return None, None

    now = dt.now(TIMEZONE)
    current_time = now.strftime("%H:%M")
    
    for prayer, display_name in PRAYER_NAMES.items():
        if prayer in prayer_times:
            prayer_time = format_time(prayer_times[prayer])
            if prayer_time > current_time:
                return display_name, prayer_time
    
    return None, None

def format_prayer_times(prayer_times: Dict[str, str]) -> Dict[str, str]:
    """Format all prayer times to HH:MM format."""
    return {
        prayer: format_time(time)
        for prayer, time in prayer_times.items()
    }
