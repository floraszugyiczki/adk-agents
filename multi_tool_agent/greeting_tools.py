from typing import Optional


def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name (str, optional): The name of the person to greet.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        return f"Hello, {name}!"
    return "Hello there!"


def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    return "Goodbye! Have a great day."