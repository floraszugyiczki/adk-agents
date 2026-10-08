from google.adk.agents import Agent
from backend.config import MODEL
from backend.agents.greeting_agent.tools.say_hello import say_hello
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history 

greeting_agent = Agent(
    name="greeting_agent",
    model=MODEL,
    description="Handles simple greetings and hellos using the 'say_hello' tool.",
    instruction=(
        "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting "
        "using the 'say_hello' tool. If the user gives their name, pass it to the tool. "
        "Do not engage in any other conversation or tasks."
    ),
    tools=[say_hello],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,       
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)