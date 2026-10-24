from google.adk.agents import Agent
from backend.config import MODEL, AGENTS
from backend.agents.time_agent.tools.time_tools import get_current_time, get_time_difference
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history

time_agent = Agent(
    name=AGENTS["time"]["name"],
    model=MODEL,
    description=AGENTS["time"]["description"],
    instruction=(
        "You are the Time Agent. Answer questions about the current local time in any city "
        "worldwide and about the time difference between two cities. Always use your tools; "
        "never guess. If a city name is ambiguous, pass the country or region along with it. "
        "If the request is not about time, transfer to the agent that can handle it."
    ),
    tools=[get_current_time, get_time_difference],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)