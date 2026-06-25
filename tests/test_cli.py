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
        allowed_tools: str | None = None,
    ) -> None:
        """Helper to create a skill directory with SKILL.md."""
        skill_dir = tmp_path / name
        skill_dir.mkdir(exist_ok=True)
        frontmatter = f"---\nname: {name}\ndescription: {description}\n"
        if allowed_tools:
            frontmatter += f"allowed-tools: {allowed_tools}\n"
        frontmatter += "---\n\nInstructions.\n"
        (skill_dir / "SKILL.md").write_text(frontmatter)

    def test_list_skills(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        self._create_skill(tmp_path, "debugger", "Debug errors")
        bot = self._make_bot(tmp_path)

        # Simulate /skills command
        from chatbot.cli import handle_command

        handle_command("/skills", bot)

        captured = capsys.readouterr()
        assert "code-review" in captured.out
        assert "debugger" in captured.out

    def test_activate_skill(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        result = handle_command("/activate code-review", bot)

        captured = capsys.readouterr()
        assert "Activated" in captured.out
        assert bot.active_skill is not None
        assert bot.active_skill.name == "code-review"
        assert result is True

    def test_activate_nonexistent_skill(self, tmp_path, capsys):
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        result = handle_command("/activate nonexistent", bot)

        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert result is True

    def test_deactivate_skill(self, tmp_path, capsys):
        self._create_skill(tmp_path, "code-review", "Review code")
        bot = self._make_bot(tmp_path)
        bot.activate_skill("code-review")

        from chatbot.cli import handle_command

        handle_command("/deactivate", bot)

        captured = capsys.readouterr()
        assert "Deactivated" in captured.out
        assert bot.active_skill is None

    def test_deactivate_when_no_skill_active(self, tmp_path, capsys):
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        handle_command("/deactivate", bot)

        captured = capsys.readouterr()
        assert "No skill" in captured.out

    def test_activate_shows_allowed_tools(self, tmp_path, capsys):
        self._create_skill(
            tmp_path, "code-review", "Review code", allowed_tools="shell_executor file_reader"
        )
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        handle_command("/activate code-review", bot)

        captured = capsys.readouterr()
        assert "shell_executor" in captured.out
        assert "file_reader" in captured.out

    def test_activate_without_name_shows_usage(self, tmp_path, capsys):
        bot = self._make_bot(tmp_path)

        from chatbot.cli import handle_command

        result = handle_command("/activate", bot)

        captured = capsys.readouterr()
        assert "Usage" in captured.out
        assert result is True
