"""Tests for llm module."""

from unittest.mock import MagicMock, patch

import pytest

from chatbot.llm import chat


class TestChat:
    """Test the chat function."""

    @pytest.mark.asyncio
    @patch("chatbot.llm.acompletion")
    async def test_returns_response_text(self, mock_acompletion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from LLM!"
        mock_response.choices[0].message.tool_calls = None
        mock_acompletion.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]

        # Act
        result = await chat(messages, model="test-model", api_key="test-key")

        # Assert
        assert result["type"] == "text"
        assert result["content"] == "Hello from LLM!"

    @pytest.mark.asyncio
    @patch("chatbot.llm.acompletion")
    async def test_passes_messages_to_llm(self, mock_acompletion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_acompletion.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        # Act
        await chat(messages, model="test-model", api_key="test-key")

        # Assert
        call_kwargs = mock_acompletion.call_args
        assert call_kwargs.kwargs["messages"] == messages

    @pytest.mark.asyncio
    @patch("chatbot.llm.acompletion")
    async def test_passes_model_and_api_key(self, mock_acompletion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_acompletion.return_value = mock_response

        # Act
        await chat(
            [{"role": "user", "content": "Hi"}],
            model="deepseek-chat",
            api_key="sk-test",
            base_url="https://api.test.com",
        )

        # Assert
        call_kwargs = mock_acompletion.call_args
        assert call_kwargs.kwargs["model"] == "deepseek-chat"
        assert call_kwargs.kwargs["api_key"] == "sk-test"
        assert call_kwargs.kwargs["api_base"] == "https://api.test.com"

    @pytest.mark.asyncio
    @patch("chatbot.llm.acompletion")
    async def test_handles_none_content(self, mock_acompletion):
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = None
        mock_acompletion.return_value = mock_response

        # Act
        result = await chat([{"role": "user", "content": "Hi"}], model="test", api_key="key")

        # Assert
        assert result["type"] == "text"
        assert result["content"] == ""
