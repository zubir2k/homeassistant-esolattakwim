"""Utility functions for eSolat Takwim Malaysia."""
from datetime import datetime, time
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
    current_time = time(now.hour, now.minute, now.second)
    
    # Convert prayer times to time objects for comparison
    prayer_time_objects = {}
    for prayer, time_str in prayer_times.items():
        try:
            time_parts = time_str.split(':')
            if len(time_parts) >= 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2]) if len(time_parts) > 2 else 0
                prayer_time_objects[prayer] = time(hour, minute, second)
        except (ValueError, IndexError):
            continue

    # Find the next prayer
    next_prayer = None
    next_time = None
    
    # First check for prayers later today
    for prayer, prayer_time in prayer_time_objects.items():
        if prayer_time > current_time:
            if next_time is None or prayer_time < next_time:
                next_prayer = PRAYER_NAMES[prayer]
                next_time = prayer_time

    # If no next prayer found today, get the first prayer of tomorrow
    if next_prayer is None:
        first_prayer = None
        first_time = None
        for prayer, prayer_time in prayer_time_objects.items():
            if first_time is None or prayer_time < first_time:
                first_prayer = PRAYER_NAMES[prayer]
                first_time = prayer_time
        next_prayer = first_prayer
        next_time = first_time

    if next_time is None:
        return None, None

    # Convert next_time back to string format
    next_time_str = next_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    return next_prayer, next_time_str

def format_prayer_times(prayer_times: Dict[str, str]) -> Dict[str, str]:
    """Format all prayer times to HH:MM format."""
    return {
        prayer: format_time(time)
        for prayer, time in prayer_times.items()
    }