"""Tool definition and registry for managing callable tools."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Tool:
    """A tool that the LLM can call.

    Attributes:
        name: Unique identifier for the tool
        description: What the tool does (shown to LLM)
        parameters: JSON Schema for the tool's parameters
        function: The actual Python function to execute
    """

    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., Any]

    def to_openai_definition(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry for managing tools that the LLM can call."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions in OpenAI function calling format."""
        return [tool.to_openai_definition() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        return tool.function(**arguments)

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())
