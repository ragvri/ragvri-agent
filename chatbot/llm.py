"""LLM provider abstraction using litellm."""

from litellm import completion


def chat(
    messages: list[dict[str, str]],
    model: str = "deepseek-chat",
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """Send messages to an LLM and return the response.

    This is a thin wrapper around litellm that handles
    the common pattern of sending messages and extracting
    the response text.
    """
    kwargs: dict = {
        "model": model,
        "messages": messages,
    }

    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url

    response = completion(**kwargs)

    return response.choices[0].message.content or ""
