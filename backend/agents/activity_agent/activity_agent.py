from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from backend.config import MODEL, AGENTS, ACTIVITY_RULES
from backend.agents.weather_agent.weather_agent import weather_agent
from backend.agents.activity_agent.tools.wikivoyage_tools import get_city_activities
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history


def activity_instruction(context) -> str:
    """Builds the instruction at runtime from ACTIVITY_RULES in config.py."""
    rules = []
    for r in ACTIVITY_RULES:
        line = f"- If {r['when']}: prefer {r['prefer']}."
        if r.get("note"):
            line += f" Also {r['note']}."
        rules.append(line)
    rules_text = "\n".join(rules)

    return (
        "You are the Activity Agent. You suggest things to do in a city, day by day, based on its weather.\n"
        "1. If the city is missing, ask the user for it. If the number of days is missing, use 3.\n"
        f"2. Ask the tool '{AGENTS['weather']['name']}' for the daily forecast of that city. "
        "Request, for each day, the lowest and highest temperature in Celsius, the chance of rain, "
        "and whether snow or thunderstorms are expected.\n"
        "3. Call 'get_city_activities' once for the city (limit 15). It returns real sights ('see') and "
        "activities ('do') from Wikivoyage, each with a name and a short description.\n"
        "4. For each day, choose the listings that fit that day's weather according to the rules below. "
        "Judge indoor or outdoor from the name and description. Use only listings that "
        "get_city_activities returned and never invent places. Do not repeat a place on another day "
        "while enough other listings are left.\n"
        f"Rules:\n{rules_text}\n"
        "5. Answer with one short block per day: the date, the weather in a few words, and 2-3 listings "
        "with a few words about each. If the user asked for one specific day, answer only for that day. "
        "End with: 'Source: Wikivoyage (CC BY-SA)'.\n"
        "If get_city_activities returns no listings or an error, say that no guide data was found for "
        "this city and give only general suggestions that fit the weather, clearly marked as general."
    )


activity_agent = Agent(
    name=AGENTS["activity"]["name"],
    model=MODEL,
    description=AGENTS["activity"]["description"],
    instruction=activity_instruction,
    tools=[AgentTool(agent=weather_agent), get_city_activities],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)