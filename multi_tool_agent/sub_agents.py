from google.adk.agents import Agent
from .config import MODEL
from .greeting_tools import say_hello, say_goodbye
from .packing_tools import get_packing_advice

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
)

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
)

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
)