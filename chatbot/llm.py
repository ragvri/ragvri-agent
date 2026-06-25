"""LLM provider abstraction using litellm."""

from typing import Any, NotRequired, TypedDict

from litellm import completion
from litellm.types.utils import ModelResponse


class ToolCall(TypedDict):
    """A single tool call request from the LLM."""

    id: str
    name: str
    arguments: str


class ChatResult(TypedDict):
    """Result from a chat completion call.

    Attributes:
        type: "text" for normal responses, "tool_calls" for tool use
        content: The text content (only when type is "text")
        tool_calls: List of tool calls (only when type is "tool_calls")
    """

    type: str
    content: NotRequired[str]
    tool_calls: NotRequired[list[ToolCall]]


def chat(
    messages: list[dict[str, Any]],
    model: str = "deepseek-chat",
    api_key: str | None = None,
    base_url: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> ChatResult:
    """Send messages to an LLM and return the response.

    Returns:
        ChatResult with:
        - type: "text" or "tool_calls"
        - content: str (for text responses)
        - tool_calls: list of ToolCall (for tool calls)
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    if tools:
        kwargs["tools"] = tools

    response: ModelResponse = completion(**kwargs)

    message = response.choices[0].message

    # Check if LLM wants to call a tool
    if message.tool_calls:
        tool_calls: list[ToolCall] = [
            {
                "id": tc.id or "",
                "name": tc.function.name or "",
                "arguments": tc.function.arguments or "",
            }
            for tc in message.tool_calls
        ]
        return {"type": "tool_calls", "tool_calls": tool_calls}

    # Regular text response
    return {"type": "text", "content": message.content or ""}
