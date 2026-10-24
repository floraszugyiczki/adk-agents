from google.adk.agents import Agent
from backend.config import MODEL, AGENTS
from backend.agents.greeting_agent.greeting_agent import greeting_agent
from backend.agents.farewell_agent.farewell_agent import farewell_agent
from backend.agents.weather_agent.weather_agent import weather_agent
from backend.agents.time_agent.time_agent import time_agent
from backend.agents.packing_agent.packing_agent import packing_agent
from backend.agents.activity_agent.activity_agent import activity_agent
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history
from backend.agents.history_agent.history_agent import history_agent

# Every sub-agent of the root. Add new agents here and in AGENTS (config.py).
SUB_AGENTS = [greeting_agent, farewell_agent, weather_agent, time_agent, packing_agent, activity_agent, history_agent]

def root_instruction(context) -> str:
    """Builds the routing instruction at runtime from the agent descriptions in config.py."""
    routes = "\n".join(
        f"- {a.name}: {a.description}" for a in SUB_AGENTS
    )
    return (
        "You are the root agent. You talk to the user and decide which specialist agent "
        "handles each request. You never answer questions yourself and you have no tools: "
        "always transfer to exactly one agent.\n"
        f"Available agents:\n{routes}\n"
        "Rules:\n"
        "- Pick the agent whose description best matches the request.\n"
        "- Questions about what to pack or wear go to the packing agent, even if they mention weather.\n"
        "- If the request is unclear, ask the user one short clarifying question.\n"
        "- If no agent fits, say briefly what you can help with."
        "- Questions about what to do, visit or see go to the activity agent.\n"
        "- If the request is unclear, ask the user one short clarifying question.\n"
        "- Requests to go back to an earlier conversation or session go to the history agent.\n"        
    )


root_agent = Agent(
    name=AGENTS["root"]["name"],
    model=MODEL,
    description=AGENTS["root"]["description"],
    instruction=root_instruction,
    sub_agents=SUB_AGENTS,
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)