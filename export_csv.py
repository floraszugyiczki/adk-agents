import csv
from sqlalchemy import select

from backend.utility.db import SessionLocal, Message

OUT = "chat_log.csv"
COLUMNS = ["id", "session_id", "timestamp", "role", "content",
           "tool_name", "tool_args", "tool_result", "error", "invocation_id"]

with SessionLocal() as db, open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(COLUMNS)
    count = 0
    for m in db.scalars(select(Message).order_by(Message.session_id, Message.id)):
        writer.writerow([getattr(m, c) for c in COLUMNS])
        count += 1

print(f"Exported {count} messages to {OUT}")