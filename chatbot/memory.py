"""Conversation memory management."""

from typing import Any


class Memory:
    """Manages conversation history as an in-memory list.

    This is the simplest form of chatbot memory:
    - Store messages in a Python list
    - Send the full history to the LLM each time
    - Trim when it gets too long
    """

    def __init__(self, system_prompt: str = "You are a helpful assistant.", max_messages: int = 50):
        self.max_messages = max_messages
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    def add(self, role: str, content: str) -> None:
        """Add a message to history."""
        self.messages.append({"role": role, "content": content})
        self._trim()

    def add_assistant_with_tool_calls(self, tool_calls: list[dict]) -> None:
        """Add an assistant message that includes tool calls."""
        self.messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": tool_calls,
            }
        )
        self._trim()

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        """Add a tool result message."""
        self.messages.append(
            {
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call_id,
            }
        )
        self._trim()

    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages (system + history)."""
        return self.messages.copy()

    def _trim(self) -> None:
        """Keep only the last N messages, always preserving system prompt."""
        if len(self.messages) > self.max_messages:
            # Keep system prompt (index 0) + last N-1 messages
            self.messages = [self.messages[0]] + self.messages[-(self.max_messages - 1) :]

    def clear(self) -> None:
        """Reset memory, keeping only the system prompt."""
        system_msg = self.messages[0]
        self.messages = [system_msg]
