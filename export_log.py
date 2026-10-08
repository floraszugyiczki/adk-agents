import sqlite3
import json

DB = "chat_log.db"
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


conn = sqlite3.connect(DB)
sessions = conn.execute(
    "SELECT session_id, started_at FROM sessions ORDER BY started_at"
).fetchall()

total = 0
with open(OUT, "w", encoding="utf-8") as f:
    for sid, started in sessions:
        f.write(f"SESSION {sid}\nstarted: {started[:19].replace('T', ' ')}\n")
        f.write("-" * 70 + "\n")
        rows = conn.execute(
            "SELECT timestamp, role, content, tool_name, tool_args, tool_result, error "
            "FROM messages WHERE session_id=? ORDER BY id",
            (sid,),
        ).fetchall()
        for ts, role, content, tool, args, result, error in rows:
            total += 1
            t = ts[11:19]  # HH:MM:SS
            if role == "user":
                f.write(f"\n[{t}] USER: {short(content, 500)}\n")
            elif role == "tool":
                if tool == "transfer_to_agent":
                    target = json.loads(args).get("agent_name") if args else "?"
                    f.write(f"[{t}]   -> delegated to {target}\n")
                else:
                    res = format_result(result)
                    f.write(f"[{t}]   tool {tool}({format_args(args)}) => {res}\n")
            else:
                f.write(f"[{t}] {role.upper()}: {short(content, 500)}\n")
            if error:
                f.write(f"[{t}]   ERROR: {error}\n")
        f.write("\n")

print(f"Exported {total} messages from {len(sessions)} session(s) to {OUT}")