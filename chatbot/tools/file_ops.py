"""File operations tools: read, write, and edit files."""

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


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing exact text.

    Performs an exact string replacement — old_text must appear exactly
    once in the file. Use read_file first to see the current content
    and craft a precise old_text.

    Args:
        path: Path to the file to edit
        old_text: Exact text to find and replace (must be unique in the file)
        new_text: Replacement text

    Returns:
        Success message with context, or an error message
    """
    try:
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"

        content = file_path.read_text()
        count = content.count(old_text)

        if count == 0:
            return (
                f"Error: old_text not found in {path}. "
                f"Make sure it matches the file content exactly "
                f"(including whitespace and indentation)."
            )
        if count > 1:
            return (
                f"Error: old_text appears {count} times in {path}. "
                f"Provide more context to make it unique (include surrounding lines)."
            )

        new_content = content.replace(old_text, new_text, 1)
        file_path.write_text(new_content)
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error editing file: {e}"


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

file_editor_tool = Tool(
    name="file_editor",
    description=(
        "Edit a file by replacing exact text. old_text must appear exactly once "
        "in the file. Use file_reader first to see current content. "
        "For small targeted changes — use file_writer for new files or full rewrites."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to edit",
            },
            "old_text": {
                "type": "string",
                "description": "Exact text to find and replace (must be unique in the file)",
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text",
            },
        },
        "required": ["path", "old_text", "new_text"],
    },
    function=edit_file,
)
