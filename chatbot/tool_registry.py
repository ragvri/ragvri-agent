"""Tool registry for managing available tools."""

from typing import Any, Callable


class ToolRegistry:
    """Registry for managing tools that the LLM can call.

    Each tool is registered with:
    - name: Unique identifier
    - description: What the tool does (for LLM)
    - parameters: JSON schema for parameters
    - function: The actual Python function to call
    """

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        function: Callable[..., Any],
    ) -> None:
        """Register a new tool."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "function": function,
        }

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions in OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        return tool["function"](**arguments)

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())
