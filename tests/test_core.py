"""Tests for core module (ChatBot)."""

from unittest.mock import patch

import pytest

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

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_send_returns_llm_response(self, mock_chat):
        mock_chat.return_value = {"type": "text", "content": "I am a helpful assistant!"}

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False)

        response = await bot.send("Hello!")

        assert response == "I am a helpful assistant!"

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_send_adds_messages_to_memory(self, mock_chat):
        mock_chat.return_value = {"type": "text", "content": "Response"}

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False)

        await bot.send("Hello!")

        messages = bot.memory.get_messages()
        # Should have: system, user, assistant
        assert len(messages) == 3
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello!"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Response"

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_send_conversational_flow(self, mock_chat):
        mock_chat.return_value = {"type": "text", "content": "Second response"}

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False)

        await bot.send("First message")
        await bot.send("Second message")

        # Verify LLM was called twice
        assert mock_chat.call_count == 2

        # Verify memory has all messages
        messages = bot.memory.get_messages()
        assert len(messages) == 5  # system + 2 user + 2 assistant


class TestChatBotReset:
    """Test the reset method."""

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_reset_clears_history(self, mock_chat):
        mock_chat.return_value = {"type": "text", "content": "Response"}

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False)

        await bot.send("Hello!")
        bot.reset()

        messages = bot.memory.get_messages()
        assert len(messages) == 1  # Only system prompt


class TestChatBotWithTools:
    """Test ChatBot with tool calling."""

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_executes_tool_and_returns_response(self, mock_chat):
        # First call: LLM wants to call calculator
        # Second call: LLM gives final response
        mock_chat.side_effect = [
            {
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "name": "calculator",
                        "arguments": '{"expression": "2+2"}',
                    }
                ],
            },
            {"type": "text", "content": "2 + 2 = 4"},
        ]

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        response = await bot.send("What is 2+2?")

        assert response == "2 + 2 = 4"
        assert mock_chat.call_count == 2

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_tool_result_added_to_memory(self, mock_chat):
        mock_chat.side_effect = [
            {
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "calculator",
                        "arguments": '{"expression": "10*5"}',
                    }
                ],
            },
            {"type": "text", "content": "10 * 5 = 50"},
        ]

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        await bot.send("What is 10*5?")

        messages = bot.memory.get_messages()
        # system + user + tool_call_assistant + tool_result + final_assistant
        assert len(messages) == 5
        assert messages[2]["role"] == "assistant"  # tool call
        assert messages[3]["role"] == "tool"  # tool result


class TestChatBotMCP:
    """Test ChatBot MCP integration."""

    def test_has_mcp_client(self):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)
        assert bot.mcp_client is not None
        assert not bot.mcp_client.is_connected

    def test_get_all_tool_definitions_includes_built_in(self):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)
        definitions = bot.get_all_tool_definitions()
        # Should have 6 built-in tools
        assert len(definitions) >= 6
        names = [d["function"]["name"] for d in definitions]
        assert "calculator" in names
        assert "get_current_datetime" in names
        assert "python_executor" in names
        assert "file_reader" in names
        assert "file_writer" in names
        assert "shell_executor" in names


class TestChatBotSkills:
    """Test ChatBot skill integration."""

    def test_loads_skills_from_directory(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Test skill\n---\n\nDo stuff.\n"
        )
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, skills_dir=tmp_path)
        assert len(bot.skills) == 1
        assert bot.skills[0].name == "my-skill"

    def test_starts_with_no_active_skill(self):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)
        assert bot.active_skill is None

    def test_activate_skill(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Test skill\n---\n\nDo stuff.\n"
        )
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, skills_dir=tmp_path)
        result = bot.activate_skill("my-skill")
        assert result is True
        assert bot.active_skill is not None
        assert bot.active_skill.name == "my-skill"

    def test_activate_nonexistent_skill(self):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)
        result = bot.activate_skill("nonexistent")
        assert result is False
        assert bot.active_skill is None

    def test_deactivate_skill(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Test skill\n---\n\nDo stuff.\n"
        )
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, skills_dir=tmp_path)
        bot.activate_skill("my-skill")
        bot.deactivate_skill()
        assert bot.active_skill is None

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_skill_prepends_instructions_to_system_prompt(self, mock_chat, tmp_path):
        mock_chat.return_value = {"type": "text", "content": "Done"}

        skill_dir = tmp_path / "code-review"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: code-review\ndescription: Review code\n---\n\n"
            "You are a senior code reviewer. Follow these steps.\n"
        )
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False, skills_dir=tmp_path)
        bot.activate_skill("code-review")

        await bot.send("Review main.py")

        # Check the messages sent to the LLM
        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"] or call_args[1]["messages"]
        system_msg = messages[0]["content"]
        assert "senior code reviewer" in system_msg

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_skill_filters_tools_by_allowed_tools(self, mock_chat, tmp_path):
        mock_chat.return_value = {"type": "text", "content": "Done"}

        skill_dir = tmp_path / "code-review"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: code-review\ndescription: Review code\n"
            "allowed-tools: shell_executor file_reader\n---\n\n"
            "Review the code.\n"
        )
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, skills_dir=tmp_path)
        bot.activate_skill("code-review")

        await bot.send("Review main.py")

        call_args = mock_chat.call_args
        tools = call_args.kwargs.get("tools") or call_args[1].get("tools")
        tool_names = [t["function"]["name"] for t in tools]
        assert "shell_executor" in tool_names
        assert "file_reader" in tool_names
        # calculator should NOT be in the filtered list
        assert "calculator" not in tool_names

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_no_skill_keeps_all_tools(self, mock_chat):
        mock_chat.return_value = {"type": "text", "content": "Done"}

        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        await bot.send("What is 2+2?")

        call_args = mock_chat.call_args
        tools = call_args.kwargs.get("tools") or call_args[1].get("tools")
        tool_names = [t["function"]["name"] for t in tools]
        # All tools should be available
        assert "calculator" in tool_names
        assert "shell_executor" in tool_names
        assert "file_reader" in tool_names

    @pytest.mark.asyncio
    @patch("chatbot.core.chat")
    async def test_skill_without_allowed_tools_keeps_all_tools(self, mock_chat, tmp_path):
        mock_chat.return_value = {"type": "text", "content": "Done"}

        skill_dir = tmp_path / "general"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: general\ndescription: General purpose\n---\n\nDo stuff.\n"
        )
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, skills_dir=tmp_path)
        bot.activate_skill("general")

        await bot.send("Hello")

        call_args = mock_chat.call_args
        tools = call_args.kwargs.get("tools") or call_args[1].get("tools")
        tool_names = [t["function"]["name"] for t in tools]
        # All tools should be available (no allowed-tools restriction)
        assert "calculator" in tool_names
        assert "shell_executor" in tool_names
