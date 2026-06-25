"""File operations tools: read and write files."""

from pathlib import Path

from chatbot.tool_registry import Tool


def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read

    Returns:
        The file contents, or an error message
    """
    try:
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"
        return file_path.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file.

    Args:
        path: Path to the file to write
        content: Content to write

    Returns:
        Success message, or an error message
    """
    try:
        file_path = Path(path).expanduser().resolve()
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Successfully written to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


# Tool definitions for registration
file_reader_tool = Tool(
    name="file_reader",
    description="Read the contents of a file at the given path.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to read",
            }
        },
        "required": ["path"],
    },
    function=read_file,
)

file_writer_tool = Tool(
    name="file_writer",
    description="Write content to a file at the given path. Creates directories if needed.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        "required": ["path", "content"],
    },
    function=write_file,
)
