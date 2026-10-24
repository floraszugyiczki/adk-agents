from google.adk.agents import Agent
from backend.config import MODEL, AGENTS
from backend.agents.weather_agent.tools.weather_tools import get_weather
from backend.agents.weather_agent.tools.forecast_tools import get_forecast
from backend.tools.preference_tools import set_temperature_unit
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history
from backend.tools.outfit_tools import show_outfit

weather_agent = Agent(
    name=AGENTS["weather"]["name"],
    model=MODEL,
    description=AGENTS["weather"]["description"],
    instruction=(
        "You are the Weather Agent. Answer questions about the current weather and the "
        "multi-day forecast in any city worldwide. Always use your tools; never guess. "
        "If a city name is ambiguous, pass the country or region along with it. "
        "Report temperatures exactly as the tool returns them; do not convert units yourself. "
        "When the user states a temperature unit preference, save it with 'set_temperature_unit'. "
        "When the user asks how the weather is or will be in a city on a specific day, also call "
        "'show_outfit' once for that city and day (day_offset 0 for today, 1 for tomorrow) and add "
        "one sentence on what to wear, based only on the items it returns. Do not call it for "
        "multi-day packing or activity requests. "
        "If the request is not about weather, transfer to the agent that can handle it."
    ),
    tools=[get_weather, get_forecast, set_temperature_unit, show_outfit],
    output_key="last_weather_report",
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)