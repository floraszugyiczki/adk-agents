from google.adk.agents import Agent
from backend.config import MODEL, AGENTS
from backend.tools.session_tools import list_past_sessions, resume_session
from backend.utility.logging import log_user, log_agent, log_tool
from backend.utility.rehydration import rehydrate_history

history_agent = Agent(
    name=AGENTS["history"]["name"],
    model=MODEL,
    description=AGENTS["history"]["description"],
    instruction=(
        "You are the History Agent. You help the user go back to earlier conversations. "
        "If the user gives a session id (or its first characters), call 'resume_session' with it. "
        "If the user asks about earlier conversations without an id, call 'list_past_sessions' and "
        "show each one with its full session id, start time and first message, then ask which one "
        "to resume. After 'resume_session' succeeds, summarize in two sentences what that "
        "conversation was about and say the user can continue from there. "
        "If a tool returns an error, report its error_message. "
        "If the request is not about earlier conversations, transfer to the agent that can handle it."
    ),
    tools=[list_past_sessions, resume_session],
    before_agent_callback=log_user,
    before_model_callback=rehydrate_history,
    after_model_callback=log_agent,
    after_tool_callback=log_tool,
)