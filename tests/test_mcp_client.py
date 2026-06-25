"""Tests for MCP client integration."""

import pytest

from chatbot.mcp_client import MCPClient


class TestMCPClientInit:
    """Test MCP client initialization."""

    def test_creates_client(self):
        client = MCPClient()
        assert client is not None

    def test_starts_disconnected(self):
        client = MCPClient()
        assert not client.is_connected

    def test_has_empty_tools_initially(self):
        client = MCPClient()
        assert client.tool_names == []


class TestMCPClientWithServer:
    """Test MCP client with actual server."""

    @pytest.mark.asyncio
    async def test_connect_and_discover_tools(self):
        """Test connecting to server and discovering tools."""
        client = MCPClient()
        try:
            await client.connect_to_server("chatbot/tools/mcp_test_server.py")
            assert client.is_connected
            assert "greet" in client.tool_names
            assert "add" in client.tool_names
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_get_definitions(self):
        """Test getting tool definitions in OpenAI format."""
        client = MCPClient()
        try:
            await client.connect_to_server("chatbot/tools/mcp_test_server.py")
            definitions = client.get_definitions()
            assert len(definitions) == 2

            # Check format
            greet_def = next(d for d in definitions if d["function"]["name"] == "greet")
            assert greet_def["type"] == "function"
            assert "name" in greet_def["function"]
            assert "description" in greet_def["function"]
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool on the MCP server."""
        client = MCPClient()
        try:
            await client.connect_to_server("chatbot/tools/mcp_test_server.py")
            tool = client.get_tool("greet")
            assert tool is not None

            # Note: MCP tools are async, but our Tool interface is sync
            # This is a limitation we'll address in integration
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_clears_tools(self):
        """Test that disconnecting clears discovered tools."""
        client = MCPClient()
        await client.connect_to_server("chatbot/tools/mcp_test_server.py")
        assert len(client.tool_names) > 0

        await client.disconnect()
        assert not client.is_connected
        assert client.tool_names == []

    @pytest.mark.asyncio
    async def test_invalid_server_script(self):
        """Test connecting to invalid server script."""
        client = MCPClient()
        with pytest.raises(ValueError, match="Cannot determine server type"):
            await client.connect_to_server("invalid.txt")
