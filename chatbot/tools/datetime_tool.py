"""Datetime tool for getting current date and time."""

from datetime import datetime

from chatbot.tool_registry import Tool


def get_current_datetime() -> str:
    """Get the current date and time.

    Returns:
        Current date and time as a formatted string
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S %A")


# Tool definition for registration
datetime_tool = Tool(
    name="get_current_datetime",
    description=(
        "Get the current date and time."
        " Use when asked about today's date, current time, or what day it is."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    function=get_current_datetime,
)
