"""Core chat loop — where the magic happens."""

import json
from pathlib import Path

from chatbot.config import Config
from chatbot.llm import chat, chat_stream
from chatbot.mcp_client import MCPClient
from chatbot.memory import Memory
from chatbot.skill import Skill, find_skill, load_skills
from chatbot.tool_registry import Tool, ToolRegistry
from chatbot.tools.calculator import calculator_tool
from chatbot.tools.code_executor import python_executor_tool
from chatbot.tools.datetime_tool import datetime_tool
from chatbot.tools.fetch_url import fetch_url_tool
from chatbot.tools.file_ops import file_editor_tool, file_reader_tool, file_writer_tool
from chatbot.tools.shell import shell_executor_tool


class ChatBot:
    """The main chatbot orchestrator.

    This class ties together:
    - Config (settings)
    - Memory (conversation history)
    - LLM (the brain)
    - Tools (the hands)
    - MCP Client (external tools via MCP protocol)
    - Skills (specialized task modes via Agent Skills)

    The flow with tools:
    1. User sends a message
    2. We add it to memory
    3. We send the full history + tools to the LLM
    4. If LLM wants to call tools:
       a. Execute each tool (built-in or MCP)
       b. Add tool results to memory
       c. Send back to LLM
       d. Loop back to step 3 (no hard cap — LLM decides when done)
    5. If LLM returns text, return it

    Skills are model-managed:
    - System prompt includes a catalog of available skills (name + description)
    - Model calls use_skill(name) to get full instructions for a skill
    - Instructions are returned as a tool result
    - Model follows the instructions for that turn
    """

    def __init__(
        self,
        config: Config | None = None,
        enable_tools: bool = True,
        skills_dir: Path | None = None,
    ):
        self.config = config or Config.from_env()
        self.skills_dir = skills_dir

        # Load skills from directory
        self.skills: list[Skill] = load_skills(skills_dir) if skills_dir else []

        # Set up tools first (system prompt needs tool catalog)
        self.tool_registry = ToolRegistry()
        self.mcp_client = MCPClient()

        if enable_tools:
            self._register_default_tools()

        # Always register use_skill if we have skills
        if self.skills:
            self._register_use_skill_tool()

        # Build system prompt with tool and skill catalogs
        system_prompt = self._build_system_prompt(self.config.system_prompt)

        self.memory = Memory(
            system_prompt=system_prompt,
            max_messages=self.config.max_history,
        )

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Build the full system prompt with skills, guidelines, and context."""
        from datetime import date

        parts = [base_prompt]

        # Guidelines (matching pi's approach)
        parts.append("")
        parts.append("Guidelines:")
        parts.append("- Use the shell tool for file operations like ls, find, grep")
        parts.append("- Be concise in your responses")
        parts.append("- Show file paths clearly when working with files")

        # Skill catalog
        if self.skills:
            parts.append("")
            parts.append("## Available Skills")
            parts.append(
                "You have access to the following skills. "
                "To use a skill, call the `use_skill` tool with the skill name."
            )
            parts.append(
                "The tool will return the full instructions. Follow them for the current task."
            )
            parts.append("")
            for skill in self.skills:
                parts.append(f"- **{skill.name}**: {skill.description}")

        # Date and working directory (like pi)
        today = date.today().isoformat()
        cwd = Path.cwd().as_posix()
        parts.append("")
        parts.append(f"Current date: {today}")
        parts.append(f"Current working directory: {cwd}")

        return "\n".join(parts)

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
        self.tool_registry.register(file_editor_tool)

        # Web tools
        self.tool_registry.register(fetch_url_tool)

    def _register_use_skill_tool(self) -> None:
        """Register the use_skill tool for model-managed skills."""

        def use_skill(name: str) -> str:
            """Get instructions for a skill by name.

            Args:
                name: The skill name to use

            Returns:
                The skill's full instructions, or an error message
            """
            skill = find_skill(self.skills, name)
            if skill is None:
                available = ", ".join(s.name for s in self.skills)
                return f"Error: Skill '{name}' not found. Available: {available}"
            return f"# Skill: {skill.name}\n\n{skill.instructions}"

        skill_names = [s.name for s in self.skills]
        skills_list = ", ".join(skill_names)
        self.tool_registry.register(
            Tool(
                name="use_skill",
                description=(
                    f"Load and follow a skill's instructions. "
                    f"Available skills: {skills_list}. "
                    f"Call this when a task matches a skill's purpose."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": f"The skill name to use. Available: {skills_list}",
                        }
                    },
                    "required": ["name"],
                },
                function=use_skill,
            )
        )

    async def connect_mcp_server(
        self, server_script: str, env: dict[str, str] | None = None
    ) -> list[str]:
        """Connect to an MCP server and add its tools.

        Args:
            server_script: Path to the MCP server script
            env: Optional environment variables for the server

        Returns:
            List of tool names added from the server
        """
        await self.mcp_client.connect_to_server(server_script, env=env)
        return self.mcp_client.tool_names

    def get_all_tool_definitions(self) -> list[dict]:
        """Get tool definitions from both built-in and MCP tools."""
        definitions = self.tool_registry.get_definitions()
        definitions.extend(self.mcp_client.get_definitions())
        return definitions

    def get_tool_catalog(self) -> str:
        """Generate a human-readable tool catalog for the system prompt."""
        catalog = []
        for tool in self.tool_registry._tools.values():
            catalog.append(f"- **{tool.name}**: {tool.description}")
        for tool in self.mcp_client._tools.values():
            catalog.append(f"- **{tool.name}** (MCP): {tool.description}")
        return "\n".join(catalog)

    async def _execute_tool(self, name: str, arguments: dict) -> str:
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
            # MCP tools are async - execute directly
            try:
                return await self.mcp_client.execute_tool(name, arguments)
            except Exception as e:
                return f"Error executing MCP tool: {e}"

        # Otherwise, use built-in tool registry
        return str(self.tool_registry.execute(name, arguments))

    def rebuild_system_prompt(self) -> None:
        """Rebuild the system prompt with current tool and skill catalogs.

        Call this after connecting MCP servers to update available tools.
        """
        system_prompt = self._build_system_prompt(self.config.system_prompt)

        # Rebuild use_skill tool if skills changed
        if self.skills:
            self._register_use_skill_tool()

        # Update the system prompt in memory
        self.memory.messages[0] = {"role": "system", "content": system_prompt}

    async def send(self, user_message: str) -> str:
        """Process a user message and return the assistant's response.

        Handles tool calling loop:
        1. Send to LLM with tool definitions
        2. If LLM requests tool calls, execute them and loop
        3. If LLM returns text, return it

        The loop has no hard iteration cap — the LLM decides when it's
        done calling tools and returns text instead. This matches how
        real coding agents (pi, Claude Code) work.
        """
        # Add user message to memory
        self.memory.add("user", user_message)

        # Get tool definitions (built-in + MCP)
        tools = self.get_all_tool_definitions()
        tools = tools or None

        # Tool calling loop — no hard cap, LLM decides when to stop
        while True:
            # Rebuild messages each iteration (memory grows with tool results)
            messages = self.memory.get_messages()

            response = await chat(
                messages=messages,
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                tools=tools,
            )

            if response["type"] == "text":
                # Regular text response - LLM is done, we're done
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
                        result_str = await self._execute_tool(tc["name"], arguments)
                    except Exception as e:
                        result_str = f"Error: {e}"

                    # Add tool result to memory with tool_call_id
                    self.memory.add_tool_result(tc["id"], result_str)

    async def send_stream(self, user_message: str):
        """Process a user message with streaming, yielding events.

        This is the streaming version of send(). It yields dictionaries
        that describe what's happening in real-time:

        - {"type": "text", "content": "..."} — text chunk
        - {"type": "tool_start", "name": "tool_name"} — tool call starting
        - {"type": "tool_end", "name": "tool_name", "result": "..."} — tool done
        - {"type": "thinking", "content": "..."} — model thinking/reasoning
        - {"type": "done", "content": "..."} — final complete response

        Args:
            user_message: The user's message

        Yields:
            Event dictionaries
        """
        # Add user message to memory
        self.memory.add("user", user_message)

        # Get tool definitions (built-in + MCP)
        tools = self.get_all_tool_definitions()
        tools = tools or None

        # Tool calling loop — no hard cap, LLM decides when to stop
        full_response = ""

        while True:
            # Rebuild messages each iteration
            messages = self.memory.get_messages()

            # Track tool calls for this iteration
            current_tool_calls: list[dict] = []
            text_buffer = ""

            # Stream the response
            async for event in chat_stream(
                messages=messages,
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                tools=tools,
            ):
                if event["type"] == "text":
                    text_buffer += event["content"]
                    yield {"type": "text", "content": event["content"]}

                elif event["type"] == "tool_call_start":
                    tool_name = event.get("tool_name", "unknown")
                    yield {"type": "tool_start", "name": tool_name}

                elif event["type"] == "tool_call_args":
                    # Accumulate args (not yielded, just tracked)
                    pass

                elif event["type"] == "tool_call_end":
                    tool_id = event.get("tool_call_id", "")
                    tool_name = event.get("tool_name", "unknown")
                    tool_args = event.get("tool_args", "")

                    current_tool_calls.append(
                        {
                            "id": tool_id,
                            "name": tool_name,
                            "args": tool_args,
                        }
                    )

                elif event["type"] == "usage":
                    # Pass through usage events
                    yield event

                elif event["type"] == "thinking":
                    # Pass through thinking events
                    yield event

            # After stream ends, check if we have tool calls to execute
            if current_tool_calls:
                # Add assistant message with tool calls
                formatted_tool_calls = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["args"],
                        },
                    }
                    for tc in current_tool_calls
                ]
                self.memory.add_assistant_with_tool_calls(formatted_tool_calls)

                # Execute each tool
                for tc in current_tool_calls:
                    try:
                        arguments = json.loads(tc["args"])
                        result_str = await self._execute_tool(tc["name"], arguments)
                    except Exception as e:
                        result_str = f"Error: {e}"

                    # Add tool result to memory
                    self.memory.add_tool_result(tc["id"], result_str)
                    yield {
                        "type": "tool_end",
                        "name": tc["name"],
                        "result": result_str[:200] + ("..." if len(result_str) > 200 else ""),
                    }

                # Continue the loop for more tool calls
                full_response += text_buffer
                continue

            else:
                # No tool calls — this is the final response
                full_response += text_buffer
                self.memory.add("assistant", full_response)
                yield {"type": "done", "content": full_response}
                return

    def reset(self) -> None:
        """Clear conversation history."""
        self.memory.clear()
