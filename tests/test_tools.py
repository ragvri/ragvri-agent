"""Tests for built-in tools."""

from chatbot.tools.calculator import calculate
from chatbot.tools.datetime_tool import get_current_datetime


class TestCalculator:
    """Test the calculator tool."""

    def test_basic_addition(self):
        result = calculate("2 + 3")
        assert result == "5"

    def test_basic_multiplication(self):
        result = calculate("4 * 5")
        assert result == "20"

    def test_complex_expression(self):
        result = calculate("(10 + 5) * 2")
        assert result == "30"

    def test_handles_floats(self):
        result = calculate("3.14 * 2")
        assert result == "6.28"

    def test_returns_string(self):
        result = calculate("1 + 1")
        assert isinstance(result, str)


class TestDatetimeTool:
    """Test the datetime tool."""

    def test_returns_string(self):
        result = get_current_datetime()
        assert isinstance(result, str)

    def test_contains_date_info(self):
        result = get_current_datetime()
        # Should contain year, month, day, time
        assert len(result) > 10
