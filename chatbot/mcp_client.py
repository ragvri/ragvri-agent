"""MCP (Model Context Protocol) client for connecting to MCP servers."""

from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from chatbot.tool_registry import Tool


class MCPClient:
    """Client for connecting to MCP servers and managing their tools.

    MCP servers expose tools via a standardized protocol. This client:
    1. Connects to MCP servers (via stdio)
    2. Discovers available tools
    3. Makes tools available to the chatbot
    """

    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._tools: dict[str, Tool] = {}

    @property
    def is_connected(self) -> bool:
        """Whether the client is connected to an MCP server."""
        return self._session is not None

    @property
    def tool_names(self) -> list[str]:
        """Get list of available tool names."""
        return list(self._tools.keys())

    async def connect_to_server(self, server_script: str) -> None:
        """Connect to an MCP server.

        Args:
            server_script: Path to the server script (.py or .js)
        """
        # Determine if Python or Node.js server
        is_python = server_script.endswith(".py")
        is_js = server_script.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script],
        )

        # Connect to the server
        self._exit_stack = AsyncExitStack()
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # Initialize the session
        await self._session.initialize()

        # Discover available tools
        await self._discover_tools()

    async def _discover_tools(self) -> None:
        """Discover tools from the connected MCP server."""
        if not self._session:
            return

        tools_response = await self._session.list_tools()
        self._tools.clear()

        for tool in tools_response.tools:
            # Convert MCP tool to our Tool format
            our_tool = Tool(
                name=tool.name,
                description=tool.description or "",
                parameters=tool.inputSchema,
                function=lambda name=tool.name, **kwargs: self._execute_mcp_tool(name, kwargs),
            )
            self._tools[tool.name] = our_tool

    async def _execute_mcp_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool on the MCP server."""
        if not self._session:
            raise ValueError("Not connected to MCP server")

        result = await self._session.call_tool(name, arguments)
        # Extract text content from result
        if result.content:
            content = result.content[0]
            if hasattr(content, "text"):
                return str(content.text)
            return str(content)
        return "No result"

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self._session = None
        self._tools.clear()

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all MCP tool definitions in OpenAI format."""
        return [tool.to_openai_definition() for tool in self._tools.values()]

    def get_tool(self, name: str) -> Tool | None:
        """Get an MCP tool by name."""
        return self._tools.get(name)
