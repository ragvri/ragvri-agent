"""Core chat loop — where the magic happens."""

import json
from typing import Any

from chatbot.config import Config
from chatbot.llm import chat
from chatbot.memory import Memory
from chatbot.tool_registry import ToolRegistry
from chatbot.tools.calculator import TOOL_DEFINITION as CALCULATOR_TOOL
from chatbot.tools.datetime_tool import TOOL_DEFINITION as DATETIME_TOOL


class ChatBot:
    """The main chatbot orchestrator.

    This class ties together:
    - Config (settings)
    - Memory (conversation history)
    - LLM (the brain)
    - Tools (the hands)

    The flow with tools:
    1. User sends a message
    2. We add it to memory
    3. We send the full history + tools to the LLM
    4. If LLM wants to call tools:
       a. Execute each tool
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

        if enable_tools:
            self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the built-in tools."""
        self.tool_registry.register(**CALCULATOR_TOOL)
        self.tool_registry.register(**DATETIME_TOOL)

    def send(self, user_message: str) -> str:
        """Process a user message and return the assistant's response.

        Handles tool calling loop:
        1. Send to LLM with tool definitions
        2. If LLM requests tool calls, execute them and loop
        3. If LLM returns text, return it
        """
        # Add user message to memory
        self.memory.add("user", user_message)

        # Get tool definitions if tools are enabled
        tools = self.tool_registry.get_definitions() if self.tool_registry.tool_names else None

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
                        result = self.tool_registry.execute(tc["name"], arguments)
                        result_str = str(result)
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
