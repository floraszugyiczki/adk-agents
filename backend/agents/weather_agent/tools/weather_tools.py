import requests
from backend.tools.geo import geocode, label
from google.adk.tools.tool_context import ToolContext

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow", 77: "snow grains",
    80: "light rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "light snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with light hail", 99: "thunderstorm with heavy hail",
}


def get_weather(city: str, tool_context: ToolContext) -> dict:
    """Retrieves the current weather for any city in the world.

    Args:
        city (str): City name. Add a country or region to disambiguate,
            e.g. "Paris, Texas" or "Springfield, Illinois".

    Returns:
        dict: status and report, or status and error_message.
    """
    try:
        place = geocode(city)
        if place is None:
            return {"status": "error", "error_message": f"Could not find a place called '{city}'."}

        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
            timeout=10,
        )
        resp.raise_for_status()
        cur = resp.json()["current"]
    except requests.RequestException as e:
        return {"status": "error", "error_message": f"Weather service request failed: {e}"}

    unit = tool_context.state.get("user_preference_temperature_unit", "Celsius")
    temp, feels = cur["temperature_2m"], cur["apparent_temperature"]
    if unit == "Fahrenheit":
        temp, feels, symbol = temp * 9 / 5 + 32, feels * 9 / 5 + 32, "°F"
    else:
        symbol = "°C"

    tool_context.state["last_city_checked"] = label(place)
    desc = WMO_CODES.get(cur["weather_code"], "unknown conditions")
    return {
        "status": "success",
        "report": (
            f"Weather in {label(place)}: {desc}, {temp:.1f} {symbol}, "
            f"feels like {feels:.1f} {symbol}, "
            f"humidity {cur['relative_humidity_2m']}%, wind {cur['wind_speed_10m']} km/h."
        ),
    }