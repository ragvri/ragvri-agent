"""LLM provider abstraction using litellm."""

from typing import Any

from litellm import completion


def chat(
    messages: list[dict[str, str]],
    model: str = "deepseek-chat",
    api_key: str | None = None,
    base_url: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Send messages to an LLM and return the response.

    This is a thin wrapper around litellm that handles
    the common pattern of sending messages and extracting
    the response text.

    Returns:
        dict with:
        - "type": "text" or "tool_calls"
        - "content": str (for text responses)
        - "tool_calls": list of tool call dicts (for tool calls)
    """
    kwargs: dict = {
        "model": model,
        "messages": messages,
    }

    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    if tools:
        kwargs["tools"] = tools

    response = completion(**kwargs)

    message = response.choices[0].message

    # Check if LLM wants to call a tool
    if message.tool_calls:
        tool_calls = []
        for tc in message.tool_calls:
            tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
            )
        return {"type": "tool_calls", "tool_calls": tool_calls}

    # Regular text response
    return {"type": "text", "content": message.content or ""}
