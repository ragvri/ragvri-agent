"""Python code execution tool."""

import subprocess
import sys
import tempfile
from pathlib import Path

from chatbot.tool_registry import Tool


def execute_python(code: str) -> str:
    """Execute Python code and return the output.

    Args:
        code: Python code to execute

    Returns:
        The output of the code, or an error message
    """
    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        # Run the code in a subprocess
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            output = result.stdout
            return output if output else "Code executed successfully (no output)"
        else:
            error = result.stderr
            return f"Error:\n{error}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30 second limit)"
    except Exception as e:
        return f"Error: {e}"
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


# Tool definition for registration
python_executor_tool = Tool(
    name="python_executor",
    description=(
        "Execute Python code and return the output."
        " Use for calculations, data processing, or any Python task."
    ),
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute",
            }
        },
        "required": ["code"],
    },
    function=execute_python,
)
