from pathlib import Path
from typing import Optional

from sqlalchemy import ForeignKey, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# backend/utility/db.py -> parents[2] is the project root
DB_PATH = Path(__file__).resolve().parents[2] / "chat_log.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)  # SessionLocal() opens a database session


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    """One conversation (same id as the ADK session)."""
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[str]]
    started_at: Mapped[Optional[str]]

    messages: Mapped[list["Message"]] = relationship(back_populates="session", order_by="Message.id")


class Message(Base):
    """One logged item: a user message, an agent reply or a tool call."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"))
    timestamp: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    tool_name: Mapped[Optional[str]] = mapped_column(Text)
    tool_args: Mapped[Optional[str]] = mapped_column(Text)
    tool_result: Mapped[Optional[str]] = mapped_column(Text)
    error: Mapped[Optional[str]] = mapped_column(Text)
    invocation_id: Mapped[Optional[str]] = mapped_column(Text)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


def init_db():
    """Create missing tables. Also adds the invocation_id column to an old database."""
    Base.metadata.create_all(engine)
    columns = [c["name"] for c in inspect(engine).get_columns("messages")]
    if "invocation_id" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE messages ADD COLUMN invocation_id TEXT"))


init_db()