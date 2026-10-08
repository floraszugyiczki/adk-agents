"""Setup check for the ADK agent team.

Run from the repository root:

    python check_setup.py

Verifies the Python version, the API key file, package imports, the agent
structure, the chat log and rehydration code (offline, on a temporary
database), and every tool against the live Open-Meteo API. It sends NO
requests to Gemini, so it does not use any model quota.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

ENV_FILE = ROOT / "backend" / ".env"
PLACEHOLDER = "PASTE_YOUR_KEY_HERE"


class FakeToolContext:
    """Minimal stand-in for ADK's ToolContext (the tools only use .state)."""

    def __init__(self):
        self.state = {}


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


def check_agent_structure():
    from backend.main import root_agent

    tool_names = [getattr(t, "__name__", str(t)) for t in root_agent.tools]
    sub_names = [a.name for a in root_agent.sub_agents]
    ok = len(sub_names) == 3 and len(tool_names) >= 5
    return ok, f"root tools={tool_names}; sub-agents={sub_names}"


def check_rehydration_import():
    from backend.utility.rehydration import MAX_MESSAGES, load_history, rehydrate_history

    ok = callable(load_history) and callable(rehydrate_history)
    return ok, f"load_history and rehydrate_history found (MAX_MESSAGES={MAX_MESSAGES})"


def check_invocation_id_column():
    from backend.utility.logging import conn

    columns = [r[1] for r in conn.execute("PRAGMA table_info(messages)")]
    return "invocation_id" in columns, f"messages columns: {', '.join(columns)}"


def check_load_history():
    """load_history() on a temporary database: order, tool rows skipped, current turn excluded."""
    import sqlite3
    import tempfile

    import backend.utility.rehydration as rehydration

    rows = [
        ("s1", "user", "Hello", None),  # logged before invocation_id existed
        ("s1", "greeting_agent", "Hi there!", None),
        ("s1", "user", "Weather in Oslo?", "inv-1"),
        ("s1", "tool", None, "inv-1"),
        ("s1", "weather_time_agent", "It is 5 °C in Oslo.", "inv-1"),
        ("s1", "user", "What did I ask?", "inv-2"),  # the current turn
        ("s2", "user", "Other session", "inv-9"),
    ]
    expected = [
        {"role": "user", "text": "Hello"},
        {"role": "model", "text": "Hi there!"},
        {"role": "user", "text": "Weather in Oslo?"},
        {"role": "model", "text": "It is 5 °C in Oslo."},
    ]
    original_conn = rehydration.conn
    with tempfile.TemporaryDirectory() as tmp:
        test_conn = sqlite3.connect(Path(tmp) / "test_log.db")
        try:
            test_conn.execute(
                "CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, "
                "role TEXT, content TEXT, invocation_id TEXT)"
            )
            test_conn.executemany(
                "INSERT INTO messages (session_id, role, content, invocation_id) VALUES (?,?,?,?)", rows
            )
            rehydration.conn = test_conn
            history = rehydration.load_history("s1", "inv-2")
        finally:
            rehydration.conn = original_conn
            test_conn.close()
    if history == expected:
        return True, f"{len(history)} messages in order, tool row and current turn skipped"
    return False, f"unexpected history: {history}"


def build_tool_checks():
    from backend.agents.farewell_agent.tools.say_goodbye import say_goodbye
    from backend.agents.greeting_agent.tools.say_hello import say_hello
    from backend.agents.packing_agent.tools.get_packing_advice import get_packing_advice
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
        ("tool get_packing_advice", lambda: get_packing_advice("Lisbon", 4)),
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
        run("agent structure", check_agent_structure),
        run("rehydration import", check_rehydration_import),
        run("log schema invocation_id", check_invocation_id_column),
        run("load_history on temp db", check_load_history),
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
