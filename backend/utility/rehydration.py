from google.genai import types

from sqlalchemy import or_, select
from backend.utility.db import SessionLocal, Message

MAX_MESSAGES = 20  # how many logged messages to restore at most


def load_history(session_id, current_invocation_id, limit=MAX_MESSAGES):
    """Read the last `limit` user/agent messages of a session from chat_log.db."""
    query = (
        select(Message.role, Message.content)
        .where(Message.session_id == session_id)
        .where(Message.role != "tool")
        .where(Message.content.is_not(None))
        .where(or_(Message.invocation_id.is_(None), Message.invocation_id != current_invocation_id))
        .order_by(Message.id.desc())
        .limit(limit)
    )
    with SessionLocal() as db:
        rows = db.execute(query).all()
    rows.reverse()  # oldest first
    history = [
        {"role": "user" if role == "user" else "model", "text": text}
        for role, text in rows
    ]
    while history and history[0]["role"] == "model":  # model input must start with the user
        history.pop(0)
    return history


def rehydrate_history(callback_context, llm_request):
    """before_model_callback: put the logged history in front of the model input
    when ADK itself has no memory of this session (e.g. after a server restart)."""
    state = callback_context.state
    session = callback_context.session
    current = callback_context.invocation_id

    if "rehydrated_history" not in state:
        has_earlier_turns = any(e.invocation_id != current for e in session.events)
        if has_earlier_turns:
            return None  # ADK already knows this conversation
        history = load_history(session.id, current)
        if not history:
            return None  # brand-new session, nothing to restore
        state["rehydrated_history"] = history  # remembered for the next turns

    restored = [
        types.Content(role=m["role"], parts=[types.Part(text=m["text"])])
        for m in state["rehydrated_history"]
    ]
    llm_request.contents = restored + llm_request.contents
    return None