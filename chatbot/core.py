"""Core chat loop — where the magic happens."""

import asyncio
import json

from chatbot.config import Config
from chatbot.llm import chat
from chatbot.mcp_client import MCPClient
from chatbot.memory import Memory
from chatbot.tool_registry import ToolRegistry
from chatbot.tools.calculator import calculator_tool
from chatbot.tools.code_executor import python_executor_tool
from chatbot.tools.datetime_tool import datetime_tool
from chatbot.tools.file_ops import file_reader_tool, file_writer_tool
from chatbot.tools.shell import shell_executor_tool


class ChatBot:
    """The main chatbot orchestrator.

    This class ties together:
    - Config (settings)
    - Memory (conversation history)
    - LLM (the brain)
    - Tools (the hands)
    - MCP Client (external tools via MCP protocol)

    The flow with tools:
    1. User sends a message
    2. We add it to memory
    3. We send the full history + tools to the LLM
    4. If LLM wants to call tools:
       a. Execute each tool (built-in or MCP)
       b. Add tool results to memory
       c. Send back to LLM for final response
    5. If LLM returns text, return it
    """

    def __init__(self, config: Config | None = None, enable_tools: bool = True):
        self.config = config or Config.from_env()
        self.memory = Memory(
            system_prompt=self.config.system_prompt,
            max_messages=self.config.max_history,
        )
        self.tool_registry = ToolRegistry()
        self.mcp_client = MCPClient()

        if enable_tools:
            self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the built-in tools."""
        # Basic tools
        self.tool_registry.register(calculator_tool)
        self.tool_registry.register(datetime_tool)

        # Code execution tools
        self.tool_registry.register(python_executor_tool)
        self.tool_registry.register(shell_executor_tool)

        # File operation tools
        self.tool_registry.register(file_reader_tool)
        self.tool_registry.register(file_writer_tool)

    async def connect_mcp_server(self, server_script: str) -> list[str]:
        """Connect to an MCP server and add its tools.

        Args:
            server_script: Path to the MCP server script

        Returns:
            List of tool names added from the server
        """
        await self.mcp_client.connect_to_server(server_script)
        return self.mcp_client.tool_names

    def get_all_tool_definitions(self) -> list[dict]:
        """Get tool definitions from both built-in and MCP tools."""
        definitions = self.tool_registry.get_definitions()
        definitions.extend(self.mcp_client.get_definitions())
        return definitions

    def _execute_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool (built-in or MCP).

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result as string
        """
        # Check if it's an MCP tool
        mcp_tool = self.mcp_client.get_tool(name)
        if mcp_tool:
            # MCP tools are async, so we need to run them
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an async context, need to handle differently
                    # For now, create a new event loop in a thread
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run, self.mcp_client._execute_mcp_tool(name, arguments)
                        )
                        result = future.result(timeout=30)
                        return str(result)
                else:
                    return loop.run_until_complete(
                        self.mcp_client._execute_mcp_tool(name, arguments)
                    )
            except Exception as e:
                return f"Error executing MCP tool: {e}"

        # Otherwise, use built-in tool registry
        return str(self.tool_registry.execute(name, arguments))

    def send(self, user_message: str) -> str:
        """Process a user message and return the assistant's response.

        Handles tool calling loop:
        1. Send to LLM with tool definitions
        2. If LLM requests tool calls, execute them and loop
        3. If LLM returns text, return it
        """
        # Add user message to memory
        self.memory.add("user", user_message)

        # Get tool definitions (built-in + MCP)
        tools = self.get_all_tool_definitions() or None

        # Tool calling loop (max 5 iterations to prevent infinite loops)
        for _ in range(5):
            response = chat(
                messages=self.memory.get_messages(),
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                tools=tools,
            )

            if response["type"] == "text":
                # Regular text response - we're done
                self.memory.add("assistant", response["content"])
                return response["content"]

            if response["type"] == "tool_calls":
                # LLM wants to call tools
                # Add the assistant's tool call message to memory
                tool_calls = response["tool_calls"]

                # Format tool calls for OpenAI-compatible API
                formatted_tool_calls = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        },
                    }
                    for tc in tool_calls
                ]
                self.memory.add_assistant_with_tool_calls(formatted_tool_calls)

                # Execute each tool and add results to memory
                for tc in tool_calls:
                    try:
                        arguments = json.loads(tc["arguments"])
                        result_str = self._execute_tool(tc["name"], arguments)
                    except Exception as e:
                        result_str = f"Error: {e}"

                    # Add tool result to memory with tool_call_id
                    self.memory.add_tool_result(tc["id"], result_str)

        # If we get here, we hit the iteration limit
        self.memory.add("assistant", "I'm sorry, I got stuck in a loop trying to use tools.")
        return "I'm sorry, I got stuck in a loop trying to use tools."

    def reset(self) -> None:
        """Clear conversation history."""
        self.memory.clear()
