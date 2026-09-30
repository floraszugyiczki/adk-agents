import requests
from .geo import geocode, label
from .weather_tools import FORECAST_URL, WMO_CODES


def get_forecast(city: str, days: int = 3) -> dict:
    """Retrieves a daily weather forecast for any city in the world.

    Args:
        city (str): City name. Add a country or region to disambiguate,
            e.g. "Paris, Texas".
        days (int): Number of days to forecast, from 1 to 7. Defaults to 3.

    Returns:
        dict: status and report, or status and error_message.
    """
    days = max(1, min(int(days), 7))
    try:
        place = geocode(city)
        if place is None:
            return {"status": "error", "error_message": f"Could not find a place called '{city}'."}

        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=10,
        )
        resp.raise_for_status()
        daily = resp.json()["daily"]
    except requests.RequestException as e:
        return {"status": "error", "error_message": f"Weather service request failed: {e}"}

    lines = []
    for i, date in enumerate(daily["time"]):
        desc = WMO_CODES.get(daily["weather_code"][i], "unknown conditions")
        lines.append(
            f"{date}: {desc}, {daily['temperature_2m_min'][i]:.0f} to "
            f"{daily['temperature_2m_max'][i]:.0f} °C, "
            f"precipitation chance {daily['precipitation_probability_max'][i]}%"
        )
    return {
        "status": "success",
        "report": f"{days}-day forecast for {label(place)}:\n" + "\n".join(lines),
    }