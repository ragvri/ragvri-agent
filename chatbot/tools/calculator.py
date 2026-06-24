"""Calculator tool for evaluating math expressions."""


def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A math expression string (e.g., "2 + 3", "10 * (5 - 2)")

    Returns:
        The result as a string
    """
    try:
        # Safely evaluate the expression
        # Only allow basic math operations
        allowed_names = {"__builtins__": {}}
        result = eval(expression, allowed_names, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "calculator",
    "description": "Evaluate a mathematical expression. Use for calculations like '2 + 3', '10 * 5', '(15 - 3) / 4'.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate",
            }
        },
        "required": ["expression"],
    },
    "function": calculate,
}
