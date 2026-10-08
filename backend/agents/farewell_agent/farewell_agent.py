from google.adk.agents import Agent
from backend.config import MODEL
from backend.agents.farewell_agent.tools.say_goodbye import say_goodbye
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history 


farewell_agent = Agent(
    name="farewell_agent",
    model=MODEL,
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
    instruction=(
        "You are the Farewell Agent. Your ONLY task is to provide a polite goodbye "
        "using the 'say_goodbye' tool when the user is leaving or ending the conversation. "
        "Do not perform any other actions."
    ),
    tools=[say_goodbye],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)