from google.adk.models import Gemini
from google.genai import types

MODEL = Gemini(
    model="gemini-3.5-flash-lite",
    retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2, max_delay=30),
)

# One place for every agent's name and description.
# The root agent routes requests based on these descriptions.
AGENTS = {
    "root": {
        "name": "root_agent",
        "description": (
            "Main coordinator. Talks to the user and routes each request "
            "to the right specialist agent."
        ),
    },
    "greeting": {
        "name": "greeting_agent",
        "description": "Handles simple greetings and hellos using the 'say_hello' tool.",
    },
    "farewell": {
        "name": "farewell_agent",
        "description": "Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
    },
    "weather": {
        "name": "weather_agent",
        "description": (
            "Answers questions about the current weather and the multi-day forecast "
            "for any city, and saves the user's temperature unit preference "
            "(Celsius or Fahrenheit)."
        ),
    },
    "time": {
        "name": "time_agent",
        "description": (
            "Answers questions about the current local time in any city "
            "and the time difference between two cities."
        ),
    },
    
    "activity": {
        "name": "activity_agent",
        "description": (
            "Suggests real sights and things to do in a city, day by day, based on its forecast, "
            "using Wikivoyage travel guide data. Pick this for 'what can I do', 'what to visit' "
            "or 'ideas for the weekend'."
        ),
    },
    "packing": {
        "name": "packing_agent",
        "description": (
    "Gives packing and clothing advice for a trip to a city. It asks the "
    "weather agent for the forecast and applies the configured packing rules."
        ),
    },
    
    "history": {
        "name": "history_agent",
        "description": (
            "Lists earlier conversations and goes back to one by session id, restoring its history "
            "so the user can continue. Pick this for 'go back to session ...', "
            "'what did we talk about earlier' or 'continue my previous conversation'."
        ),
    },    

}

# Packing rules. The packing agent reads these and decides itself what to recommend.
# To change the advice, edit this list only. No code change needed.
PACKING_RULES = [
    {"when": "the lowest temperature is below 0 °C",
     "pack": ["heavy winter coat", "gloves", "scarf", "hat", "thermal underwear"]},
    {"when": "the lowest temperature is between 0 and 10 °C",
     "pack": ["warm jacket", "sweater", "long trousers"]},
    {"when": "the highest temperature is between 10 and 20 °C",
     "pack": ["light jacket", "long-sleeved tops"]},
    {"when": "the highest temperature is between 20 and 28 °C",
     "pack": ["t-shirts", "light trousers or skirt", "sunglasses"]},
    {"when": "the highest temperature is above 28 °C",
     "pack": ["light breathable clothes", "sun hat", "sunscreen", "water bottle"]},
    {"when": "the chance of rain is 50% or more",
     "pack": ["umbrella", "waterproof jacket"]},
    {"when": "snow is expected",
     "pack": ["waterproof boots", "warm socks"]},
    {"when": "thunderstorms are expected",
     "pack": ["waterproof jacket"],
     "note": "warn the user to avoid exposed outdoor plans"},
]

# Activity rules. The activity agent reads these and decides itself what to suggest per day.
# "prefer" tells the agent which kind of Wikivoyage listings (see/do) fit that weather.
ACTIVITY_RULES = [
    {"when": "the day is dry (rain chance below 30%) and the highest temperature is between 12 and 28 °C",
     "prefer": "outdoor listings: walks, parks, viewpoints, sights in the open air, tours, cycling"},
    {"when": "the highest temperature is above 28 °C",
     "prefer": "water or shade: beaches, pools, parks, early-morning or evening outdoor visits, air-conditioned museums around midday",
     "note": "mention drinking water and shade"},
    {"when": "the highest temperature is below 5 °C",
     "prefer": "warm indoor listings: thermal baths, museums, galleries, cafes, theatres"},
    {"when": "the chance of rain is 50% or more",
     "prefer": "indoor listings: museums, galleries, theatres, cinemas, covered markets, indoor sights"},
    {"when": "snow is expected",
     "prefer": "snow-friendly listings: viewpoints, parks, winter activities, plus warm indoor places"},
    {"when": "thunderstorms are expected",
     "prefer": "indoor listings only",
     "note": "warn against hiking, beaches and open areas"},
]

OUTFIT_THRESHOLDS = {
    "shorts_from": 24,      # felt temperature (°C): shorts at or above this
    "tshirt_from": 19,      # t-shirt at or above this, long sleeve below
    "jacket_below": 16,     # jacket below this
    "coat_below": 4,        # coat + scarf + beanie + gloves below this
    "cold_morning": 8,      # lowest felt temperature of the day: jacket even if the day is warm
    "rain_prob": 50,        # % chance of precipitation
    "rain_mm": 1.0,         # mm of precipitation per day
    "heavy_rain_mm": 10,    # mm: waterproof boots
    "windy_kmh": 30,        # wind speed
    "gust_kmh": 50,         # wind gusts: umbrella is unusable
    "uv_high": 6,           # UV index: sunglasses + cap
    "uv_moderate": 3,       # UV index: sunglasses when it is also warm
}