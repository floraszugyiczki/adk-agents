from google.adk.tools.tool_context import ToolContext


def set_temperature_unit(unit: str, tool_context: ToolContext) -> dict:
    """Saves the user's preferred temperature unit for this session.

    Args:
        unit (str): Either "Celsius" or "Fahrenheit".

    Returns:
        dict: status and report, or status and error_message.
    """
    normalized = unit.strip().lower()
    if normalized in ("celsius", "c"):
        value = "Celsius"
    elif normalized in ("fahrenheit", "f"):
        value = "Fahrenheit"
    else:
        return {"status": "error", "error_message": "Unit must be Celsius or Fahrenheit."}
    tool_context.state["user_preference_temperature_unit"] = value
    return {"status": "success", "report": f"Temperature unit set to {value}."}