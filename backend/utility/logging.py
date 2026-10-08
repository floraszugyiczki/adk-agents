import sqlite3
import json
from datetime import datetime
from pathlib import Path

# backend/utility/logging.py -> parents[2] is the project root
DB_PATH = Path(__file__).resolve().parents[2] / "chat_log.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.executescript("""
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id    TEXT,
    started_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id),
    timestamp   TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT,
    tool_name   TEXT,
    tool_args   TEXT,
    tool_result TEXT,
    error       TEXT,
    invocation_id TEXT
);
""")
    

if "invocation_id" not in [r[1] for r in conn.execute("PRAGMA table_info(messages)")]:
    conn.execute("ALTER TABLE messages ADD COLUMN invocation_id TEXT")
    conn.commit()

def ensure_session(sid, user_id="user"):
    conn.execute("INSERT OR IGNORE INTO sessions VALUES (?,?,?)",
                 (sid, user_id, datetime.now().isoformat()))
    conn.commit()


def log_message(sid, role, content=None, tool_name=None,
                tool_args=None, tool_result=None, error=None,
                invocation_id=None):
    ensure_session(sid)
    conn.execute(
        "INSERT INTO messages (session_id, timestamp, role, content, "
        "tool_name, tool_args, tool_result, error, invocation_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (sid, datetime.now().isoformat(), role, content, tool_name,
         json.dumps(tool_args, default=str) if tool_args else None,
         json.dumps(tool_result, default=str) if tool_result else None,
         error, invocation_id))
    conn.commit()


# ---- ADK callbacks ----
_seen_invocations = set()


def log_user(callback_context):
    inv = callback_context.invocation_id
    if inv in _seen_invocations:
        return None
    _seen_invocations.add(inv)
    content = callback_context.user_content
    if content and content.parts:
        text = "".join(p.text for p in content.parts if p.text)
        if text:
            log_message(callback_context.session.id, "user", text,
                        invocation_id=callback_context.invocation_id)
    return None


def log_agent(callback_context, llm_response):
    if llm_response.content and llm_response.content.parts:
        text = "".join(p.text for p in llm_response.content.parts if p.text)
        if text:
            log_message(callback_context.session.id, callback_context.agent_name, text,
                        invocation_id=callback_context.invocation_id)
    return None


def log_tool(tool, args, tool_context, tool_response):
    log_message(tool_context.session.id, "tool", tool_name=tool.name,
                tool_args=args, tool_result=tool_response,
                invocation_id=tool_context.invocation_id)
    return None