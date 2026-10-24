from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from backend.config import MODEL, AGENTS, PACKING_RULES
from backend.agents.weather_agent.weather_agent import weather_agent
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history


def packing_instruction(context) -> str:
    """Builds the instruction at runtime from PACKING_RULES in config.py."""
    rules = []
    for r in PACKING_RULES:
        line = f"- If {r['when']}: pack {', '.join(r['pack'])}."
        if r.get("note"):
            line += f" Also {r['note']}."
        rules.append(line)
    rules_text = "\n".join(rules)

    return (
        "You are the Packing Agent. You give packing advice for a trip.\n"
        "1. If the city or the dates are missing, ask the user for them.\n"
        f"2. Ask the tool '{AGENTS['weather']['name']}' for the forecast of that city. "
        "Request the lowest and highest temperature in Celsius, the chance of rain, "
        "and whether snow or thunderstorms are expected.\n"
        "3. Decide yourself what to pack by applying ALL matching rules below to that forecast. "
        "Do not invent weather data; use only what the weather tool returned.\n"
        f"Rules:\n{rules_text}\n"
        "4. Answer with a short, combined packing list and one line explaining which weather it is based on."
    )


packing_agent = Agent(
    name=AGENTS["packing"]["name"],
    model=MODEL,
    description=AGENTS["packing"]["description"],
    instruction=packing_instruction,
    tools=[AgentTool(agent=weather_agent)],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)