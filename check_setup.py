"""Setup check for the ADK agent team.

Run from the repository root:

    python check_setup.py

Verifies the Python version, the API key file, package imports, the agent
structure and every tool against the live Open-Meteo API. It sends NO
requests to Gemini, so it does not use any model quota.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

ENV_FILE = ROOT / "multi_tool_agent" / ".env"
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
        return False, "multi_tool_agent/.env not found - copy multi_tool_agent/.env.example to multi_tool_agent/.env"
    try:
        text = ENV_FILE.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False, "multi_tool_agent/.env is not UTF-8 - recreate it in a text editor"
    for line in text.splitlines():
        if line.strip().startswith("GOOGLE_API_KEY"):
            value = line.split("=", 1)[-1].strip().strip('"').strip("'")
            if value and value != PLACEHOLDER:
                return True, "GOOGLE_API_KEY is set"
    return False, "GOOGLE_API_KEY is missing or still the placeholder"


def check_agent_structure():
    from multi_tool_agent.agent import root_agent

    tool_names = [getattr(t, "__name__", str(t)) for t in root_agent.tools]
    sub_names = [a.name for a in root_agent.sub_agents]
    ok = len(sub_names) == 3 and len(tool_names) >= 5
    return ok, f"root tools={tool_names}; sub-agents={sub_names}"


def build_tool_checks():
    from multi_tool_agent.forecast_tools import get_forecast
    from multi_tool_agent.greeting_tools import say_goodbye, say_hello
    from multi_tool_agent.packing_tools import get_packing_advice
    from multi_tool_agent.preference_tools import set_temperature_unit
    from multi_tool_agent.time_tools import get_current_time, get_time_difference
    from multi_tool_agent.weather_tools import get_weather

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
