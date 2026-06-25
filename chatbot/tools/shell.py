"""Shell command execution tool."""

import subprocess

from chatbot.tool_registry import Tool


def execute_shell(command: str) -> str:
    """Execute a shell command and return the output.

    Args:
        command: Shell command to execute

    Returns:
        The output of the command, or an error message
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            output = result.stdout
            return output if output else "Command executed successfully (no output)"
        else:
            error = result.stderr
            return f"Error:\n{error}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30 second limit)"
    except Exception as e:
        return f"Error: {e}"


# Tool definition for registration
shell_executor_tool = Tool(
    name="shell_executor",
    description=(
        "Execute a shell command and return the output."
        " Use for file operations, git commands, or system tasks."
    ),
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            }
        },
        "required": ["command"],
    },
    function=execute_shell,
)
