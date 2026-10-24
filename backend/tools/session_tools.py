from google.adk.tools import ToolContext
from sqlalchemy import select

from backend.session_manager import SessionManager
from backend.utility.db import ChatSession, SessionLocal
from backend.utility.rehydration import load_history

_manager = SessionManager()  # only used for its list_sessions query
SHOWN_CHARS = 300


def list_past_sessions(limit: int = 10) -> dict:
    """Lists earlier conversations, newest first, with session id, start time,
    number of logged messages and the first user message.

    Args:
        limit (int): How many sessions to list, 1 to 50. Defaults to 10.

    Returns:
        dict: status and a list 'sessions'.
    """
    limit = max(1, min(int(limit), 50))
    return {"status": "success", "sessions": _manager.list_sessions(limit)}


def resume_session(session_id: str, tool_context: ToolContext) -> dict:
    """Goes back to an earlier conversation: loads its messages as context for this chat,
    so the conversation can continue from there.

    Args:
        session_id (str): The full session id, or its first characters if unique.

    Returns:
        dict: status, the full session id, and the restored messages (shortened).
    """
    sid = session_id.strip()
    with SessionLocal() as db:
        if db.get(ChatSession, sid) is None:
            matches = db.scalars(select(ChatSession.session_id).where(ChatSession.session_id.startswith(sid))).all()
            if len(matches) != 1:
                return {"status": "error",
                        "error_message": f"No unique session found for '{session_id}' ({len(matches)} matches)."}
            sid = matches[0]

    history = load_history(sid, current_invocation_id="")
    if not history:
        return {"status": "error", "error_message": f"Session {sid} has no logged messages."}

    tool_context.state["rehydrated_history"] = history  # rehydrate_history puts this in front of every model call
    shortened = [{"role": m["role"], "text": m["text"][:SHOWN_CHARS]} for m in history]
    return {"status": "success", "session_id": sid, "messages_restored": len(history), "history": shortened}