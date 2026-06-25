"""Tests for CLI skill commands."""

from pathlib import Path

from chatbot.config import Config
from chatbot.core import ChatBot


class TestCLISkillCommands:
    """Test skill-related CLI command handling."""

    def _make_bot(self, tmp_path: Path) -> ChatBot:
        """Create a ChatBot with skills loaded from tmp_path."""
        config = Config(model="test", api_key="key", base_url="http://test")
        return ChatBot(config=config, enable_tools=False, skills_dir=tmp_path)

    def _create_skill(
        self,
        tmp_path: Path,
        name: str,
        description: str = "A skill",
    ) -> None:
        """Helper to create a skill directory with SKILL.md."""
        skill_dir = tmp_path / name
        skill_dir.mkdir(exist_ok=True)
        frontmatter = f"---\nname: {name}\ndescription: {description}\n"
        frontmatter += "---\n\nInstructions.\n"
        (skill_dir / "SKILL.md").write_text(frontmatter)

    def test_list_skills(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        self._create_skill(tmp_path, "debugger", "Debug errors")
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        handle_command("/skills", bot)

        captured = capsys.readouterr()
        assert "code-review" in captured.out
        assert "debugger" in captured.out

    def test_list_skills_when_empty(self, tmp_path, capsys):
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        handle_command("/skills", bot)

        captured = capsys.readouterr()
        assert "No skills available" in captured.out

    def test_skill_with_name(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        result = handle_command("/skill code-review", bot)

        captured = capsys.readouterr()
        assert "Using skill" in captured.out
        assert "code-review" in captured.out
        assert result is True

    def test_skill_with_nonexistent_name(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        result = handle_command("/skill nonexistent", bot)

        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert result is True

    def test_skill_without_name_shows_list(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        self._create_skill(tmp_path, "debugger", "Debug errors")
        bot = self._make_bot(tmp_path)

        from unittest.mock import patch

        from chatbot.cli import handle_command

        # Mock stdin to simulate user pressing Enter (empty input)
        with patch("builtins.input", return_value=""):
            result = handle_command("/skill", bot)

        captured = capsys.readouterr()
        assert "Pick a skill" in captured.out
        assert "code-review" in captured.out
        assert "debugger" in captured.out
        assert result is True

    def test_skill_when_no_skills(self, tmp_path, capsys):
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        result = handle_command("/skill", bot)

        captured = capsys.readouterr()
        assert "No skills available" in captured.out
        assert result is True

    def test_skill_shows_description(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code for bugs")
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        handle_command("/skill code-review", bot)

        captured = capsys.readouterr()
        assert "Review code for bugs" in captured.out


class TestCLIToolsCommand:
    """Test /tools command."""

    def test_list_tools(self, capsys):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        from chatbot.cli import handle_command

        handle_command("/tools", bot)

        captured = capsys.readouterr()
        assert "calculator" in captured.out
        assert "file_reader" in captured.out
        assert "fetch_url" in captured.out


class TestCLIMCPCommand:
    """Test /mcp command."""

    def test_mcp_when_not_connected(self, capsys):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config)

        from chatbot.cli import handle_command

        handle_command("/mcp", bot)

        captured = capsys.readouterr()
        assert "No MCP servers connected" in captured.out


class TestCLIBasicCommands:
    """Test basic CLI commands."""

    def test_reset(self, capsys):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False)

        from chatbot.cli import handle_command

        handle_command("/reset", bot)

        captured = capsys.readouterr()
        assert "reset" in captured.out

    def test_unknown_command(self, capsys):
        config = Config(model="test", api_key="key", base_url="http://test")
        bot = ChatBot(config=config, enable_tools=False)

        from chatbot.cli import handle_command

        handle_command("/foobar", bot)

        captured = capsys.readouterr()
        assert "Unknown command" in captured.out
