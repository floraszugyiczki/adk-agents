import requests
from backend.tools.geo import geocode, label
from backend.agents.weather_agent.tools.weather_tools import FORECAST_URL

SNOW_CODES = {71, 73, 75, 77, 85, 86}
THUNDER_CODES = {95, 96, 99}


def get_packing_advice(city: str, days: int = 3) -> dict:
    """Builds a packing list for a trip to any city, based on its weather forecast.

    Args:
        city (str): Destination city. Add a country or region to disambiguate,
            e.g. "Paris, Texas".
        days (int): Length of the trip in days, from 1 to 7. Defaults to 3.

    Returns:
        dict: status, a report summarizing the forecast and a list of items,
            or status and error_message.
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

    lows = [v for v in daily["temperature_2m_min"] if v is not None]
    highs = [v for v in daily["temperature_2m_max"] if v is not None]
    if not lows or not highs:
        return {"status": "error", "error_message": f"No forecast data available for '{city}'."}

    rain_prob = max([v for v in daily["precipitation_probability_max"] if v is not None] or [0])
    codes = set(daily["weather_code"])
    swings = [
        hi - lo
        for hi, lo in zip(daily["temperature_2m_max"], daily["temperature_2m_min"])
        if hi is not None and lo is not None
    ]
    tmin, tmax = min(lows), max(highs)

    items = []
    if tmin < 0:
        items += ["heavy winter coat", "gloves", "hat and scarf", "thermal base layer"]
    elif tmin < 10:
        items += ["warm jacket", "sweater"]
    elif tmin < 18:
        items += ["light jacket"]

    if tmax >= 28:
        items += ["light breathable clothing", "sunglasses", "sunscreen", "water bottle"]
    elif tmax >= 20:
        items += ["t-shirts", "sunglasses"]
    else:
        items += ["long-sleeved tops"]

    if swings and max(swings) >= 12:
        items.append("extra layers for big day/night temperature swings")
    if rain_prob >= 50:
        items += ["umbrella", "waterproof jacket"]
    if codes & SNOW_CODES:
        items.append("waterproof boots")
    if codes & THUNDER_CODES:
        items.append("a plan for indoor activities (thunderstorms possible)")

    items = list(dict.fromkeys(items))
    return {
        "status": "success",
        "report": (
            f"{days}-day trip to {label(place)}: lows down to {tmin:.0f} °C, "
            f"highs up to {tmax:.0f} °C, max rain chance {rain_prob}%. "
            f"Suggested items: {', '.join(items)}."
        ),
        "items": items,
    }