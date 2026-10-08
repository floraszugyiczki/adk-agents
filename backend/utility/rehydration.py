from google.genai import types

from backend.utility.logging import conn

MAX_MESSAGES = 20  # how many logged messages to restore at most


def load_history(session_id, current_invocation_id, limit=MAX_MESSAGES):
    """Read the last `limit` user/agent messages of a session from chat_log.db."""
    rows = conn.execute(
        "SELECT role, content FROM messages "
        "WHERE session_id = ? AND role != 'tool' AND content IS NOT NULL "
        "AND (invocation_id IS NULL OR invocation_id != ?) "
        "ORDER BY id DESC LIMIT ?",
        (session_id, current_invocation_id, limit),
    ).fetchall()
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