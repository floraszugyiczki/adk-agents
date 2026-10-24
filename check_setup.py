"""Setup check for the ADK agent team.

Run from the repository root:

    python check_setup.py

Verifies the Python version, the API key file, the config, the agent tree (a router
root with five sub-agents), the instruction builders, the chat log (SQLAlchemy models),
rehydration, the session manager (offline, on a temporary database) and every tool
against the live Open-Meteo API. It sends NO requests to Gemini, so it does not use
any model quota.
"""
import asyncio
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

ENV_FILE = ROOT / "backend" / ".env"
PLACEHOLDER = "PASTE_YOUR_KEY_HERE"


class FakeToolContext:
    """Minimal stand-in for ADK's ToolContext (the tools only use .state)."""

    def __init__(self):
        self.state = {}


@contextmanager
def temp_database():
    """A throw-away SQLite database with the real tables. Yields a session factory."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.utility.db import Base

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        engine = create_engine(f"sqlite:///{Path(tmp) / 'test_log.db'}")
        Base.metadata.create_all(engine)
        try:
            yield sessionmaker(bind=engine)
        finally:
            engine.dispose()


def check_python():
    ok = sys.version_info >= (3, 10)
    return ok, f"Python {sys.version.split()[0]} (3.10+ required)"


def check_env_file():
    if not ENV_FILE.exists():
        return False, "backend/.env not found - copy .env.example to backend/.env"
    try:
        text = ENV_FILE.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False, "backend/.env is not UTF-8 - recreate it in a text editor"
    for line in text.splitlines():
        if line.strip().startswith("GOOGLE_API_KEY"):
            value = line.split("=", 1)[-1].strip().strip('"').strip("'")
            if value and value != PLACEHOLDER:
                return True, "GOOGLE_API_KEY is set"
    return False, "GOOGLE_API_KEY is missing or still the placeholder"


def check_config():
    from backend.config import AGENTS, MODEL, PACKING_RULES

    expected = {"root", "greeting", "farewell", "weather", "time", "packing"}
    missing = expected - set(AGENTS)
    bad_agents = [k for k, v in AGENTS.items() if not v.get("name") or not v.get("description")]
    bad_rules = [r for r in PACKING_RULES if not r.get("when") or not r.get("pack")]
    ok = not missing and not bad_agents and PACKING_RULES and not bad_rules
    return ok, f"MODEL={MODEL}; {len(AGENTS)} agents in config; {len(PACKING_RULES)} packing rules"


def check_agent_structure():
    from google.adk.tools.agent_tool import AgentTool

    from backend.config import AGENTS
    from backend.main import root_agent

    sub_names = [a.name for a in root_agent.sub_agents]
    expected = [AGENTS[k]["name"] for k in ("greeting", "farewell", "weather", "time", "packing")]
    packing = next(a for a in root_agent.sub_agents if a.name == AGENTS["packing"]["name"])
    packing_calls_weather = any(
        isinstance(t, AgentTool) and t.agent.name == AGENTS["weather"]["name"] for t in packing.tools
    )
    ok = not root_agent.tools and sorted(sub_names) == sorted(expected) and packing_calls_weather
    return ok, f"root tools={len(root_agent.tools)}; sub-agents={sub_names}; packing uses weather agent={packing_calls_weather}"


def check_instructions():
    from backend.agents.packing_agent.packing_agent import packing_instruction
    from backend.config import AGENTS, PACKING_RULES
    from backend.main import root_instruction

    root_text = root_instruction(None)
    packing_text = packing_instruction(None)
    routes_ok = all(AGENTS[k]["name"] in root_text for k in AGENTS if k != "root")
    rules_ok = all(r["pack"][0] in packing_text for r in PACKING_RULES)
    return routes_ok and rules_ok, "root instruction lists every sub-agent; packing instruction contains every rule"


def check_log_schema():
    from sqlalchemy import inspect

    from backend.utility.db import engine

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    columns = [c["name"] for c in inspector.get_columns("messages")] if "messages" in tables else []
    ok = "sessions" in tables and "invocation_id" in columns
    return ok, f"tables={tables}; messages columns: {', '.join(columns)}"


def check_rehydration_import():
    from backend.utility.rehydration import MAX_MESSAGES, load_history, rehydrate_history

    ok = callable(load_history) and callable(rehydrate_history)
    return ok, f"load_history and rehydrate_history found (MAX_MESSAGES={MAX_MESSAGES})"


def check_load_history():
    """load_history() on a temporary database: order, tool rows skipped, current turn excluded."""
    import backend.utility.rehydration as rehydration
    from backend.utility.db import ChatSession, Message

    rows = [
        ("s1", "user", "Hello", None),  # logged before invocation_id existed
        ("s1", "greeting_agent", "Hi there!", None),
        ("s1", "user", "Weather in Oslo?", "inv-1"),
        ("s1", "tool", None, "inv-1"),
        ("s1", "weather_agent", "It is 5 °C in Oslo.", "inv-1"),
        ("s1", "user", "What did I ask?", "inv-2"),  # the current turn
        ("s2", "user", "Other session", "inv-9"),
    ]
    expected = [
        {"role": "user", "text": "Hello"},
        {"role": "model", "text": "Hi there!"},
        {"role": "user", "text": "Weather in Oslo?"},
        {"role": "model", "text": "It is 5 °C in Oslo."},
    ]
    now = datetime.now().isoformat()
    original = rehydration.SessionLocal
    with temp_database() as factory:
        with factory() as db:
            db.add_all([ChatSession(session_id="s1"), ChatSession(session_id="s2")])
            db.flush()
            db.add_all([Message(session_id=s, timestamp=now, role=r, content=c, invocation_id=i)
                        for s, r, c, i in rows])
            db.commit()
        rehydration.SessionLocal = factory
        try:
            history = rehydration.load_history("s1", "inv-2")
        finally:
            rehydration.SessionLocal = original
    if history == expected:
        return True, f"{len(history)} messages in order, tool row and current turn skipped"
    return False, f"unexpected history: {history}"


def check_session_manager():
    """create / resume / list on a temporary database (ADK sessions stay in memory)."""
    import backend.session_manager as sm_module
    from backend.utility.db import ChatSession, Message

    async def scenario(manager):
        new_id = await manager.create()
        await manager.resume("old-session")
        try:
            await manager.resume("does-not-exist")
            raised = False
        except ValueError:
            raised = True
        return new_id, raised

    original = sm_module.SessionLocal
    with temp_database() as factory:
        with factory() as db:
            db.add(ChatSession(session_id="old-session", started_at=datetime.now().isoformat()))
            db.flush()
            db.add(Message(session_id="old-session", timestamp=datetime.now().isoformat(),
                           role="user", content="first question"))
            db.commit()
        sm_module.SessionLocal = factory
        try:
            manager = sm_module.SessionManager()
            new_id, raised = asyncio.run(scenario(manager))
            listed = manager.list_sessions()
        finally:
            sm_module.SessionLocal = original
    ok = bool(new_id) and raised and listed and listed[0]["messages"] == 1 \
        and listed[0]["first_message"] == "first question"
    return ok, f"new session created, old one resumed, unknown id rejected, list_sessions={len(listed)} row"


def build_tool_checks():
    from backend.agents.farewell_agent.tools.say_goodbye import say_goodbye
    from backend.agents.greeting_agent.tools.say_hello import say_hello
    from backend.agents.time_agent.tools.time_tools import get_current_time, get_time_difference
    from backend.agents.weather_agent.tools.forecast_tools import get_forecast
    from backend.agents.weather_agent.tools.weather_tools import get_weather
    from backend.tools.preference_tools import set_temperature_unit

    ctx = FakeToolContext()

    def weather_uses_state():
        set_temperature_unit("Fahrenheit", ctx)
        result = get_weather("Budapest", ctx)
        stored = ctx.state.get("last_city_checked")
        if result.get("status") == "success" and "°F" in result["report"] and stored:
            return True, result["report"]
        return False, f"unexpected result: {result}"

    return [
        ("tool get_weather + state", weather_uses_state),
        ("tool get_forecast", lambda: get_forecast("Reykjavik", 3)),
        ("tool get_current_time", lambda: get_current_time("Ulaanbaatar")),
        ("tool get_time_difference", lambda: get_time_difference("Budapest", "Tokyo")),
        ("tool say_hello", lambda: say_hello("Flora")),
        ("tool say_goodbye", lambda: say_goodbye()),
        ("unknown city handled", lambda: (
            get_weather("Xyzzyville", FakeToolContext()).get("status") == "error",
            "returns an error dict instead of crashing",
        )),
    ]


def run(name, fn):
    try:
        result = fn()
        if isinstance(result, tuple):
            ok, detail = result
        elif isinstance(result, dict):
            ok = result.get("status") == "success"
            detail = result.get("report") or result.get("error_message", "")
        else:
            ok, detail = bool(result), str(result)
    except Exception as exc:  # report any failure as a FAIL line
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    first_line = str(detail).splitlines()[0] if str(detail) else ""
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {first_line[:110]}")
    return ok


def main():
    results = [
        run("python version", check_python),
        run("api key file", check_env_file),
        run("config", check_config),
        run("agent structure", check_agent_structure),
        run("instruction builders", check_instructions),
        run("log schema (SQLAlchemy)", check_log_schema),
        run("rehydration import", check_rehydration_import),
        run("load_history on temp db", check_load_history),
        run("session manager on temp db", check_session_manager),
    ]
    try:
        for name, fn in build_tool_checks():
            results.append(run(name, fn))
    except Exception as exc:
        print(f"[FAIL] importing tools: {type(exc).__name__}: {exc}")
        results.append(False)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())