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

    Supported server types:
    - Python scripts (.py)
    - Node.js scripts (.js)
    - npm packages (via npx, e.g., "@modelcontextprotocol/server-github")
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

    async def connect_to_server(
        self,
        server: str,
        env: dict[str, str] | None = None,
    ) -> None:
        """Connect to an MCP server.

        Args:
            server: Server identifier. Can be:
                - Path to .py or .js file
                - npm package name (starts with @ or contains /)
            env: Optional environment variables for the server
        """
        # Determine server type and build command
        if server.endswith(".py"):
            command = "python"
            args = [server]
        elif server.endswith(".js"):
            command = "node"
            args = [server]
        elif "/" in server or server.startswith("@"):
            # Looks like an npm package
            command = "npx"
            args = ["-y", server]
        else:
            raise ValueError(
                f"Cannot determine server type for '{server}'. "
                "Use .py/.js file path or npm package name."
            )

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
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
            # Note: MCP tools don't have a local function - execution happens via execute_tool()
            our_tool = Tool(
                name=tool.name,
                description=tool.description or "",
                parameters=tool.inputSchema,
                function=None,  # MCP tools execute via the server
            )
            self._tools[tool.name] = our_tool

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result as string
        """
        if not self._session:
            raise ValueError("Not connected to MCP server")

        if name not in self._tools:
            raise ValueError(f"MCP tool '{name}' not found")

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
