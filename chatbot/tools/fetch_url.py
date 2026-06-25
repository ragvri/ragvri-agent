"""Fetch URL tool — fetch web page content and return readable text."""

import subprocess

from chatbot.tool_registry import Tool


def fetch_url(url: str) -> str:
    """Fetch a URL and return readable content.

    Uses curl to fetch the page, then extracts readable text.
    Returns the content as markdown-formatted text.

    Args:
        url: The URL to fetch

    Returns:
        The page content as text, or an error message
    """
    try:
        # Use curl with reasonable defaults
        result = subprocess.run(
            [
                "curl",
                "-sL",  # silent, follow redirects
                "-m",
                "30",  # 30 second timeout
                "-H",
                "User-Agent: Mozilla/5.0 (compatible; ChatbotAgent/1.0)",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=35,
        )

        if result.returncode != 0:
            return f"Error fetching URL: {result.stderr}"

        content = result.stdout
        if not content:
            return "Error: Empty response from URL"

        # Basic HTML stripping for readability
        # If it looks like HTML, strip tags
        if "<html" in content.lower() or "<body" in content.lower():
            content = _strip_html(content)

        # Truncate very long responses
        max_length = 50000
        if len(content) > max_length:
            content = content[:max_length] + f"\n\n[Content truncated at {max_length} characters]"

        return content

    except subprocess.TimeoutExpired:
        return "Error: Request timed out (35 second limit)"
    except Exception as e:
        return f"Error fetching URL: {e}"


def _strip_html(html: str) -> str:
    """Basic HTML tag stripping for readability."""
    import re

    # Remove script and style elements
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    # Replace common block elements with newlines
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</p>", "\n\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</div>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</h[1-6]>", "\n\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</li>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<hr[^>]*>", "\n---\n", html, flags=re.IGNORECASE)

    # Strip remaining tags
    html = re.sub(r"<[^>]+>", "", html)

    # Decode common HTML entities
    html = html.replace("&amp;", "&")
    html = html.replace("&lt;", "<")
    html = html.replace("&gt;", ">")
    html = html.replace("&quot;", '"')
    html = html.replace("&#39;", "'")
    html = html.replace("&nbsp;", " ")

    # Clean up whitespace
    html = re.sub(r"\n{3,}", "\n\n", html)
    html = re.sub(r" +", " ", html)
    html = html.strip()

    return html


# Tool definition for registration
fetch_url_tool = Tool(
    name="fetch_url",
    description=(
        "Fetch a web URL and return the page content as readable text. "
        "Use to read documentation, articles, GitHub repos, or any web page."
    ),
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch",
            }
        },
        "required": ["url"],
    },
    function=fetch_url,
)
