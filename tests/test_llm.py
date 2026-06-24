"""Tests for llm module."""

from unittest.mock import MagicMock, patch

from chatbot.llm import chat


class TestChat:
    """Test the chat function."""

    @patch("chatbot.llm.completion")
    def test_returns_response_text(self, mock_completion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from LLM!"
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]

        # Act
        result = chat(messages, model="test-model", api_key="test-key")

        # Assert
        assert result == "Hello from LLM!"
        mock_completion.assert_called_once()

    @patch("chatbot.llm.completion")
    def test_passes_messages_to_llm(self, mock_completion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        # Act
        chat(messages, model="test-model", api_key="test-key")

        # Assert
        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["messages"] == messages

    @patch("chatbot.llm.completion")
    def test_passes_model_and_api_key(self, mock_completion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        # Act
        chat(
            [{"role": "user", "content": "Hi"}],
            model="deepseek-chat",
            api_key="sk-test",
            base_url="https://api.test.com",
        )

        # Assert
        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["model"] == "deepseek-chat"
        assert call_kwargs.kwargs["api_key"] == "sk-test"
        assert call_kwargs.kwargs["api_base"] == "https://api.test.com"

    @patch("chatbot.llm.completion")
    def test_handles_none_content(self, mock_completion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_completion.return_value = mock_response

        # Act
        result = chat([{"role": "user", "content": "Hi"}], model="test", api_key="key")

        # Assert
        assert result == ""
