import uuid

from google.adk.sessions import InMemorySessionService
from sqlalchemy import func, select

from backend.utility.db import SessionLocal, ChatSession, Message

APP_NAME = "weather_assistant"
USER_ID = "user"


class SessionManager:
    """Creates, resumes and lists chat sessions.

    ADK keeps live sessions in memory (lost on restart). The messages of every session
    are also logged in chat_log.db, so a resumed session gets its history back
    through rehydrate_history (before_model_callback).
    """

    def __init__(self):
        self.service = InMemorySessionService()

    async def create(self) -> str:
        """Start a new session and return its id."""
        session = await self.service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=str(uuid.uuid4())
        )
        return session.id

    async def resume(self, session_id: str) -> str:
        """Continue an existing session by id. Raises ValueError if it was never logged."""
        with SessionLocal() as db:
            if db.get(ChatSession, session_id) is None:
                raise ValueError(f"No session with id {session_id}")
        existing = await self.service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        if existing is None:  # e.g. after a restart: new empty ADK session, history comes from the DB
            await self.service.create_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=session_id
            )
        return session_id

    def list_sessions(self, limit: int = 10) -> list[dict]:
        """The most recent sessions with message count and first user message."""
        query = (
            select(ChatSession.session_id, ChatSession.started_at, func.count(Message.id))
            .join(Message, Message.session_id == ChatSession.session_id, isouter=True)
            .group_by(ChatSession.session_id)
            .order_by(ChatSession.started_at.desc())
            .limit(limit)
        )
        result = []
        with SessionLocal() as db:
            for sid, started, count in db.execute(query).all():
                first = db.scalars(
                    select(Message.content)
                    .where(Message.session_id == sid, Message.role == "user")
                    .order_by(Message.id)
                    .limit(1)
                ).first()
                result.append({"session_id": sid, "started_at": started,
                               "messages": count, "first_message": first})
        return result