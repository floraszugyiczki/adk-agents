from google.adk.agents import Agent
from .config import MODEL
from .weather_tools import get_weather
from .forecast_tools import get_forecast
from .time_tools import get_current_time, get_time_difference
from .preference_tools import set_temperature_unit
from .sub_agents import greeting_agent, farewell_agent, packing_agent

root_agent = Agent(
    name="weather_time_agent",
    model=MODEL,
    description=(
        "Main coordinator. Answers weather, forecast and time questions for any city "
        "and delegates greetings, farewells and packing advice to specialist sub-agents."
    ),
    instruction=(
        "You are the main agent coordinating a team. Your job is to answer questions about "
        "the current weather, the multi-day forecast and the local time in any city worldwide, "
        "and the time difference between two cities. Always use your tools; never guess. "
        "If a city name is ambiguous, pass the country or region along with it. "
        "Report temperatures exactly as the tool returns them; do not convert units yourself. "
        "When the user states a temperature unit preference, save it with 'set_temperature_unit'. "
        "You have three sub-agents: "
        "1. 'greeting_agent' handles simple greetings like 'Hi' or 'Hello'. Delegate to it. "
        "2. 'farewell_agent' handles simple farewells like 'Bye' or 'See you'. Delegate to it. "
        "3. 'packing_agent' handles what to pack or wear for a trip. Delegate to it. "
        "Handle weather, forecast and time requests yourself. "
        "For anything else, say that you cannot help with it."
    ),
    tools=[get_weather, get_forecast, get_current_time, get_time_difference, set_temperature_unit],
    sub_agents=[greeting_agent, farewell_agent, packing_agent],
    output_key="last_weather_report"
)