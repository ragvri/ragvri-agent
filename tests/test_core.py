"""Tests for core module (ChatBot)."""

from unittest.mock import MagicMock, patch

from chatbot.config import Config
from chatbot.core import ChatBot


class TestChatBotInit:
    """Test ChatBot initialization."""

    def test_creates_with_default_config(self):
        with patch.object(Config, "from_env") as mock_from_env:
            mock_from_env.return_value = Config(
                model="test", api_key="test", base_url="http://test"
            )
            bot = ChatBot()
            assert bot.config.model == "test"

    def test_creates_with_provided_config(self):
        config = Config(model="custom", api_key="key", base_url="http://custom")
        bot = ChatBot(config=config)
        assert bot.config.model == "custom"

    def test_memory_has_system_prompt(self):
        config = Config(
            model="test",
            api_key="key",
            base_url="http://test",
            system_prompt="Test assistant",
        )
        bot = ChatBot(config=config)
        messages = bot.memory.get_messages()
        assert messages[0]["content"] == "Test assistant"


class TestChatBotSend:
    """Test the send method."""

    @patch("chatbot.core.chat")
    def test_send_returns_llm_response(self, mock_chat):
        mock_chat.return_value = "I am a helpful assistant!"

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        response = bot.send("Hello!")

        assert response == "I am a helpful assistant!"

    @patch("chatbot.core.chat")
    def test_send_adds_messages_to_memory(self, mock_chat):
        mock_chat.return_value = "Response"

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        bot.send("Hello!")

        messages = bot.memory.get_messages()
        # Should have: system, user, assistant
        assert len(messages) == 3
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello!"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Response"

    @patch("chatbot.core.chat")
    def test_send_conversational_flow(self, mock_chat):
        mock_chat.return_value = "Second response"

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        bot.send("First message")
        bot.send("Second message")

        # Verify LLM was called twice
        assert mock_chat.call_count == 2

        # Verify memory has all messages
        messages = bot.memory.get_messages()
        assert len(messages) == 5  # system + 2 user + 2 assistant


class TestChatBotReset:
    """Test the reset method."""

    @patch("chatbot.core.chat")
    def test_reset_clears_history(self, mock_chat):
        mock_chat.return_value = "Response"

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        bot.send("Hello!")
        bot.reset()

        messages = bot.memory.get_messages()
        assert len(messages) == 1  # Only system prompt
