"""Tests for tool registry."""

import pytest

from chatbot.tool_registry import ToolRegistry


class TestToolRegistryInit:
    """Test registry initialization."""

    def test_starts_empty(self):
        registry = ToolRegistry()
        assert registry.tool_names == []

    def test_get_definitions_empty(self):
        registry = ToolRegistry()
        assert registry.get_definitions() == []


class TestToolRegistryRegister:
    """Test registering tools."""

    def test_register_adds_tool(self):
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            function=lambda: "result",
        )
        assert "test_tool" in registry.tool_names

    def test_register_multiple_tools(self):
        registry = ToolRegistry()
        registry.register(
            name="tool1",
            description="First tool",
            parameters={"type": "object", "properties": {}},
            function=lambda: "1",
        )
        registry.register(
            name="tool2",
            description="Second tool",
            parameters={"type": "object", "properties": {}},
            function=lambda: "2",
        )
        assert len(registry.tool_names) == 2

    def test_get_tool_returns_tool(self):
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            function=lambda: "result",
        )
        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool["name"] == "test_tool"

    def test_get_tool_returns_none_for_missing(self):
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None


class TestToolRegistryDefinitions:
    """Test getting tool definitions in OpenAI format."""

    def test_get_definitions_format(self):
        registry = ToolRegistry()
        registry.register(
            name="calculator",
            description="Calculate math expressions",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"],
            },
            function=lambda expression: eval(expression),
        )

        definitions = registry.get_definitions()
        assert len(definitions) == 1

        defn = definitions[0]
        assert defn["type"] == "function"
        assert defn["function"]["name"] == "calculator"
        assert defn["function"]["description"] == "Calculate math expressions"
        assert "expression" in defn["function"]["parameters"]["properties"]


class TestToolRegistryExecute:
    """Test executing tools."""

    def test_execute_calls_function(self):
        registry = ToolRegistry()
        registry.register(
            name="add",
            description="Add two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
            function=lambda a, b: a + b,
        )

        result = registry.execute("add", {"a": 2, "b": 3})
        assert result == 5

    def test_execute_raises_on_missing_tool(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="not found"):
            registry.execute("nonexistent", {})

    def test_execute_with_no_args(self):
        registry = ToolRegistry()
        registry.register(
            name="get_time",
            description="Get current time",
            parameters={"type": "object", "properties": {}},
            function=lambda: "2024-01-01",
        )

        result = registry.execute("get_time", {})
        assert result == "2024-01-01"
