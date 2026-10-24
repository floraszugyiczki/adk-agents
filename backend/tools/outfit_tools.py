import requests
from backend.config import OUTFIT_THRESHOLDS as T
from backend.tools.geo import geocode
import re
from google.adk.tools import ToolContext
from google.genai import types
from backend.tools.outfit_figure import render_svg

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = [
    "weather_code",
    "temperature_2m_max", "temperature_2m_min",
    "apparent_temperature_max", "apparent_temperature_min",
    "precipitation_probability_max", "precipitation_sum", "snowfall_sum",
    "wind_speed_10m_max", "wind_gusts_10m_max",
    "uv_index_max",
]


def get_outfit_forecast(city: str, days: int = 7) -> dict:
    """Gets the daily forecast fields needed to decide what to wear.

    Args:
        city (str): City name.
        days (int): Number of forecast days, 1 to 16. Defaults to 7.

    Returns:
        dict: status, city, country and a list 'days' with one dict per day.
    """
    days = max(1, min(int(days), 16))
    try:
        place = geocode(city)
        if not place:
            return {"status": "error", "error_message": f"Could not find a place called '{city}'."}
        lat = place.get("latitude") or place.get("lat")
        lon = place.get("longitude") or place.get("lon")
        resp = requests.get(
            FORECAST_URL,
            params={"latitude": lat, "longitude": lon, "daily": ",".join(DAILY_FIELDS),
                    "timezone": "auto", "forecast_days": days},
            timeout=10,
        )
        resp.raise_for_status()
        daily = resp.json()["daily"]
    except (requests.RequestException, KeyError) as exc:
        return {"status": "error", "error_message": f"Forecast request failed: {exc}"}

    rows = [{"date": t, **{f: daily[f][i] for f in DAILY_FIELDS}} for i, t in enumerate(daily["time"])]
    return {"status": "success", "city": place["name"], "country": place.get("country"), "days": rows}

SNOW_CODES = {71, 73, 75, 77, 85, 86}
STORM_CODES = {95, 96, 99}


def decide_outfit(day: dict) -> dict:
    """Decides what to wear on one forecast day. Returns items (in layer order) and a reason for each."""
    hi = day["apparent_temperature_max"]
    lo = day["apparent_temperature_min"]
    feel = 0.65 * hi + 0.35 * lo          # daytime weighted felt temperature
    pop = day["precipitation_probability_max"] or 0
    rain_mm = day["precipitation_sum"] or 0
    snow_cm = day["snowfall_sum"] or 0
    wind = day["wind_speed_10m_max"] or 0
    gust = day["wind_gusts_10m_max"] or 0
    uv = day["uv_index_max"] or 0
    code = day["weather_code"]

    snowing = snow_cm > 0 or code in SNOW_CODES
    raining = (pop >= T["rain_prob"] or rain_mm >= T["rain_mm"]) and not snowing
    windy = wind >= T["windy_kmh"] or gust >= T["gust_kmh"]

    outfit: dict[str, str] = {}

    def add(item: str, reason: str):
        outfit.setdefault(item, reason)

    add("tshirt" if feel >= T["tshirt_from"] else "longsleeve", f"feels like {feel:.0f}°C")
    add("shorts" if feel >= T["shorts_from"] else "trousers", f"feels like {feel:.0f}°C")

    if feel < T["coat_below"]:
        add("coat", f"feels like {feel:.0f}°C")
        add("scarf", "cold")
        add("beanie", "cold")
        add("gloves", "cold")
    elif feel < T["jacket_below"]:
        add("jacket", f"feels like {feel:.0f}°C")
    elif lo <= T["cold_morning"]:
        add("jacket", f"it feels like {lo:.0f}°C at the coldest point of the day")

    if windy and feel < 20:
        add("jacket", f"wind up to {max(wind, gust):.0f} km/h")
    if windy and feel < 10:
        add("scarf", "wind and cold")

    if snowing:
        add("boots", "snow")
        add("gloves", "snow")
        add("beanie", "snow")

    notes = []
    if code in STORM_CODES:
        notes.append("thunderstorm forecast: avoid open areas and stay indoors during the storm")

    if raining:
        needs_raincoat = gust >= T["gust_kmh"] or (
            (windy or code in STORM_CODES) and feel < T["shorts_from"]
        )
        if needs_raincoat:
            add("raincoat", "rain with wind or storm; an umbrella is not practical")
            if "coat" not in outfit:
                outfit.pop("jacket", None)   # the raincoat is the outer layer
        else:
            add("umbrella", f"{pop:.0f}% chance of rain, {rain_mm:.1f} mm")
        if rain_mm >= T["heavy_rain_mm"]:
            add("boots", f"heavy rain, {rain_mm:.0f} mm")

    if uv >= T["uv_high"]:
        add("sunglasses", f"UV index {uv:.0f}")
        if "beanie" not in outfit:
            add("cap", f"UV index {uv:.0f}")
    elif uv >= T["uv_moderate"] and feel >= T["tshirt_from"]:
        add("sunglasses", f"UV index {uv:.0f}")

    return {"items": list(outfit), "reasons": outfit, "notes": notes, "feels_like": round(feel, 1)}

async def show_outfit(city: str, tool_context: ToolContext, day_offset: int = 0) -> dict:
    """Shows an animated figure wearing the right clothes for a city's weather on one day.

    Args:
        city (str): City name.
        day_offset (int): 0 for today, 1 for tomorrow, and so on, up to 15. Defaults to 0.

    Returns:
        dict: status, date, feels_like, items worn with the reason for each, and notes.
    """
    day_offset = max(0, min(int(day_offset), 15))
    forecast = get_outfit_forecast(city, days=day_offset + 1)
    if forecast["status"] != "success":
        return forecast

    day = forecast["days"][day_offset]
    outfit = decide_outfit(day)
    caption = f"{forecast['city']} · {day['date']} · feels like {outfit['feels_like']}°C"
    svg = render_svg(outfit["items"], caption)

    filename = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"outfit_{forecast['city']}_{day['date']}") + ".svg"
    await tool_context.save_artifact(
        filename, types.Part.from_bytes(data=svg.encode("utf-8"), mime_type="image/svg+xml")
    )
    return {
        "status": "success", "city": forecast["city"], "date": day["date"],
        "feels_like": outfit["feels_like"], "items": outfit["items"],
        "reasons": outfit["reasons"], "notes": outfit["notes"],
        "report": f"Outfit figure saved as artifact {filename}.",
    }