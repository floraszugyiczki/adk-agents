from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")  # backend/.env, same file adk web uses

import argparse
import asyncio

from google.adk.runners import Runner
from google.genai import types

from backend.main import root_agent
from backend.session_manager import APP_NAME, USER_ID, SessionManager

class AssistantRunner:
    """Sends user messages to the root agent, which routes them to the right sub-agent."""

    def __init__(self, session_manager: SessionManager):
        self.sessions = session_manager
        self.runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_manager.service,
        )

    async def ask(self, session_id: str, text: str) -> tuple[str, str]:
        """Run one turn. Returns (name of the agent that answered, answer text)."""
        message = types.Content(role="user", parts=[types.Part(text=text)])
        author, answer = root_agent.name, ""
        async for event in self.runner.run_async(
            user_id=USER_ID, session_id=session_id, new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                reply = "".join(p.text for p in event.content.parts if p.text)
                if reply:
                    author, answer = event.author, reply
        return author, answer


async def chat(resume_id=None):
    sessions = SessionManager()
    assistant = AssistantRunner(sessions)
    if resume_id:
        session_id = await sessions.resume(resume_id)
        print(f"Resumed session {session_id}")
    else:
        session_id = await sessions.create()
        print(f"New session {session_id}")
    print("Type 'exit' to quit.\n")

    while True:
        text = input("You: ").strip()
        if text.lower() in ("exit", "quit"):
            break
        if not text:
            continue
        agent, answer = await assistant.ask(session_id, text)
        print(f"[{agent}] {answer}\n")


def main():
    parser = argparse.ArgumentParser(description="Chat with the weather/time/packing assistant.")
    parser.add_argument("--resume", metavar="SESSION_ID", help="continue an earlier session")
    parser.add_argument("--list", action="store_true", help="list recent sessions and exit")
    args = parser.parse_args()

    if args.list:
        for s in SessionManager().list_sessions():
            print(f"{s['session_id']}  {s['started_at'][:19]}  {s['messages']:>3} msgs  {s['first_message']}")
        return
    asyncio.run(chat(args.resume))


if __name__ == "__main__":
    main()