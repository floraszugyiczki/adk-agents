import json
from sqlalchemy import select

from backend.utility.db import SessionLocal, ChatSession, Message

OUT = "chat_log.txt"
MAX_RESULT = 90  # max characters of a tool result shown in the text file


def short(text, limit):
    text = " ".join(str(text).split())  # collapse newlines and extra spaces
    return text if len(text) <= limit else text[: limit - 3] + "..."


def format_args(raw):
    if not raw:
        return ""
    try:
        d = json.loads(raw)
        return ", ".join(f"{k}={v}" for k, v in d.items())
    except Exception:
        return short(raw, 60)


def format_result(raw):
    if not raw:
        return ""
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            text = d.get("report") or d.get("error_message") or d.get("status") or d
        else:
            text = d
    except Exception:
        text = raw
    return short(text, MAX_RESULT)


total = 0
with SessionLocal() as db, open(OUT, "w", encoding="utf-8") as f:
    sessions = db.scalars(select(ChatSession).order_by(ChatSession.started_at)).all()
    for s in sessions:
        f.write(f"SESSION {s.session_id}\nstarted: {s.started_at[:19].replace('T', ' ')}\n")
        f.write("-" * 70 + "\n")
        for m in s.messages:  # relationship, already ordered by id
            total += 1
            t = m.timestamp[11:19]  # HH:MM:SS
            if m.role == "user":
                f.write(f"\n[{t}] USER: {short(m.content, 500)}\n")
            elif m.role == "tool":
                if m.tool_name == "transfer_to_agent":
                    target = json.loads(m.tool_args).get("agent_name") if m.tool_args else "?"
                    f.write(f"[{t}]   -> delegated to {target}\n")
                else:
                    f.write(f"[{t}]   tool {m.tool_name}({format_args(m.tool_args)}) => {format_result(m.tool_result)}\n")
            else:
                f.write(f"[{t}] {m.role.upper()}: {short(m.content, 500)}\n")
            if m.error:
                f.write(f"[{t}]   ERROR: {m.error}\n")
        f.write("\n")

print(f"Exported {total} messages from {len(sessions)} session(s) to {OUT}")