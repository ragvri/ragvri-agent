"""LLM provider abstraction using litellm with streaming support."""

from collections.abc import AsyncIterator
from typing import Any, NotRequired, TypedDict

from litellm import acompletion
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


class StreamEvent(TypedDict, total=False):
    """An event from the streaming response.

    Attributes:
        type: "text", "tool_call_start", "tool_call_args", "tool_call_end", "thinking", "usage"
        content: Text content (for type="text" or type="thinking")
        tool_call_id: ID of the tool call (for tool_call events)
        tool_name: Name of the tool (for tool_call_start)
        tool_args_delta: Incremental arguments (for tool_call_args)
        prompt_tokens: Number of prompt tokens used (for type="usage")
        completion_tokens: Number of completion tokens used (for type="usage")
        total_tokens: Total tokens used (for type="usage")
    """

    type: str
    content: NotRequired[str]
    tool_call_id: NotRequired[str]
    tool_name: NotRequired[str]
    tool_args_delta: NotRequired[str]
    prompt_tokens: NotRequired[int]
    completion_tokens: NotRequired[int]
    total_tokens: NotRequired[int]


async def chat_stream(
    messages: list[dict[str, Any]],
    model: str = "deepseek-chat",
    api_key: str | None = None,
    base_url: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> AsyncIterator[StreamEvent]:
    """Stream messages to an LLM and yield events.

    Yields StreamEvent objects with:
    - type="text": text content chunks
    - type="tool_call_start": beginning of a tool call
    - type="tool_call_args": incremental tool call arguments
    - type="tool_call_end": tool call complete

    Args:
        messages: Conversation messages
        model: Model identifier
        api_key: API key
        base_url: API base URL
        tools: Tool definitions

    Yields:
        StreamEvent objects
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        "drop_params": True,
        "allowed_openai_params": ["tools", "tool_choice"],
    }

    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    if tools:
        kwargs["tools"] = tools

    response = await acompletion(**kwargs)

    # Track tool calls being built
    tool_calls: dict[int, ToolCall] = {}
    # Track usage from chunks
    usage_prompt = 0
    usage_completion = 0

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue

        # Handle thinking/reasoning content
        reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "thinking", None)
        if reasoning:
            yield {"type": "thinking", "content": reasoning}

        # Handle text content
        if delta.content:
            yield {"type": "text", "content": delta.content}

        # Handle tool calls
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index or 0

                # New tool call starting
                if tc.id and tc.function and tc.function.name:
                    tool_calls[idx] = {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": "",
                    }
                    yield {
                        "type": "tool_call_start",
                        "tool_call_id": tc.id,
                        "tool_name": tc.function.name,
                    }

                # Incremental arguments
                if tc.function and tc.function.arguments and idx in tool_calls:
                    tool_calls[idx]["arguments"] += tc.function.arguments
                    yield {
                        "type": "tool_call_args",
                        "tool_call_id": tool_calls[idx]["id"],
                        "tool_args_delta": tc.function.arguments,
                    }

        # Capture usage if available in chunk
        if hasattr(chunk, "usage") and chunk.usage:
            usage_prompt = getattr(chunk.usage, "prompt_tokens", 0) or 0
            usage_completion = getattr(chunk.usage, "completion_tokens", 0) or 0

    # Try to get usage from response object if not found in chunks
    if usage_prompt == 0 and hasattr(response, "usage") and response.usage:
        usage_prompt = getattr(response.usage, "prompt_tokens", 0) or 0
        usage_completion = getattr(response.usage, "completion_tokens", 0) or 0

    # Emit tool_call_end events for all completed tool calls
    for idx in sorted(tool_calls.keys()):
        tc = tool_calls[idx]
        yield {
            "type": "tool_call_end",
            "tool_call_id": tc["id"],
            "tool_name": tc["name"],
            "tool_args": tc["arguments"],
        }

    # Emit usage event
    yield {
        "type": "usage",
        "prompt_tokens": usage_prompt,
        "completion_tokens": usage_completion,
        "total_tokens": usage_prompt + usage_completion,
    }


async def chat(
    messages: list[dict[str, Any]],
    model: str = "deepseek-chat",
    api_key: str | None = None,
    base_url: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> ChatResult:
    """Send messages to an LLM and return the response (non-streaming).

    This is the fallback for when streaming is not needed.

    Returns:
        ChatResult with:
        - type: "text" or "tool_calls"
        - content: str (for text responses)
        - tool_calls: list of ToolCall (for tool calls)
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "drop_params": True,
        "allowed_openai_params": ["tools", "tool_choice"],
    }

    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    if tools:
        kwargs["tools"] = tools

    response: ModelResponse = await acompletion(**kwargs)

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
