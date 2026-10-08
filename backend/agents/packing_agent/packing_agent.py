from google.adk.agents import Agent
from backend.config import MODEL
from backend.agents.packing_agent.tools.get_packing_advice import get_packing_advice
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history 


packing_agent = Agent(
    name="packing_agent",
    model=MODEL,
    description=(
        "Gives packing and clothing advice for a trip to a city, based on its "
        "forecast, using the 'get_packing_advice' tool."
    ),
    instruction=(
        "You are the Packing Agent. Your ONLY task is to advise what to pack for a trip. "
        "Use the 'get_packing_advice' tool with the destination city and the number of days. "
        "If the user gives no length, use the default. Present the result as a short, "
        "clear packing list and mention the key weather facts behind it. "
        "Do not handle any other requests."
    ),
    tools=[get_packing_advice],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history, 
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)