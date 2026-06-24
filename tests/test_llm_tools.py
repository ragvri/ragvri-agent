"""Tests for LLM tool calling integration."""

from unittest.mock import MagicMock, patch

from chatbot.llm import chat


class TestChatWithTools:
    """Test chat function with tool support."""

    @patch("chatbot.llm.completion")
    def test_passes_tools_to_llm(self, mock_completion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Calculate math",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        messages = [{"role": "user", "content": "What is 2+2?"}]

        # Act
        chat(messages, model="test", api_key="key", tools=tools)

        # Assert
        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["tools"] == tools

    @patch("chatbot.llm.completion")
    def test_returns_tool_calls_when_present(self, mock_completion):
        # Arrange
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{"expression": "2+2"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "What is 2+2?"}]

        # Act
        result = chat(messages, model="test", api_key="key", tools=[])

        # Assert
        assert result["type"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"
        assert result["tool_calls"][0]["name"] == "calculator"
        assert result["tool_calls"][0]["arguments"] == '{"expression": "2+2"}'

    @patch("chatbot.llm.completion")
    def test_returns_text_when_no_tool_calls(self, mock_completion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.tool_calls = None
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]

        # Act
        result = chat(messages, model="test", api_key="key")

        # Assert
        assert result["type"] == "text"
        assert result["content"] == "Hello!"
