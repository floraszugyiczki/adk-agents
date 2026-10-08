import datetime
from zoneinfo import ZoneInfo

import requests
from backend.tools.geo import geocode, label


def _resolve(city: str):
    """Return (place, ZoneInfo) or (None, error_dict)."""
    try:
        place = geocode(city)
    except requests.RequestException as e:
        return None, {"status": "error", "error_message": f"Geocoding request failed: {e}"}
    if place is None or not place.get("timezone"):
        return None, {"status": "error", "error_message": f"Could not find a timezone for '{city}'."}
    return place, ZoneInfo(place["timezone"])


def get_current_time(city: str) -> dict:
    """Returns the current local time in any city in the world.

    Args:
        city (str): City name. Add a country or region to disambiguate,
            e.g. "Paris, Texas".

    Returns:
        dict: status and report, or status and error_message.
    """
    place, tz = _resolve(city)
    if place is None:
        return tz
    now = datetime.datetime.now(tz)
    return {
        "status": "success",
        "report": f"The current time in {label(place)} is {now.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}.",
    }


def get_time_difference(city_a: str, city_b: str) -> dict:
    """Returns the current time difference in hours between two cities.

    Args:
        city_a (str): The first city.
        city_b (str): The second city.

    Returns:
        dict: status and report, or status and error_message.
    """
    place_a, tz_a = _resolve(city_a)
    if place_a is None:
        return tz_a
    place_b, tz_b = _resolve(city_b)
    if place_b is None:
        return tz_b
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = (now.astimezone(tz_b).utcoffset() - now.astimezone(tz_a).utcoffset()).total_seconds() / 3600
    return {
        "status": "success",
        "report": f"{label(place_b)} is {diff:+.1f} hours relative to {label(place_a)}.",
    }