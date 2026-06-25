"""Tests for skill module — loading and parsing Agent Skills."""

from pathlib import Path

from chatbot.skill import Skill, find_skill, load_skills


class TestSkillDataclass:
    """Test the Skill dataclass."""

    def test_skill_has_name(self):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="Do the thing.",
        )
        assert skill.name == "test-skill"

    def test_skill_has_description(self):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="Do the thing.",
        )
        assert skill.description == "A test skill"

    def test_skill_has_instructions(self):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="Do the thing.",
        )
        assert skill.instructions == "Do the thing."

    def test_skill_allowed_tools_defaults_to_none(self):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="Do the thing.",
        )
        assert skill.allowed_tools is None

    def test_skill_with_allowed_tools(self):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="Do the thing.",
            allowed_tools=["shell_executor", "file_reader"],
        )
        assert skill.allowed_tools == ["shell_executor", "file_reader"]


class TestLoadSkills:
    """Test loading skills from a directory."""

    def test_loads_skill_from_directory(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: my-skill\n"
            "description: Does something cool\n"
            "---\n"
            "\n"
            "Here are the instructions.\n"
        )
        skills = load_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "my-skill"
        assert skills[0].description == "Does something cool"
        assert skills[0].instructions == "Here are the instructions."

    def test_loads_multiple_skills(self, tmp_path: Path):
        for name in ["skill-a", "skill-b"]:
            skill_dir = tmp_path / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: {name} desc\n---\n\nInstructions for {name}.\n"
            )
        skills = load_skills(tmp_path)
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert names == {"skill-a", "skill-b"}

    def test_parses_allowed_tools(self, tmp_path: Path):
        skill_dir = tmp_path / "code-review"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: code-review\n"
            "description: Review code\n"
            "allowed-tools: shell_executor file_reader\n"
            "---\n"
            "\n"
            "Review the code.\n"
        )
        skills = load_skills(tmp_path)
        assert skills[0].allowed_tools == ["shell_executor", "file_reader"]

    def test_allowed_tools_none_when_not_specified(self, tmp_path: Path):
        skill_dir = tmp_path / "general"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: general\ndescription: General purpose\n---\n\nDo stuff.\n"
        )
        skills = load_skills(tmp_path)
        assert skills[0].allowed_tools is None

    def test_ignores_non_skill_directories(self, tmp_path: Path):
        # A directory without SKILL.md should be skipped
        (tmp_path / "not-a-skill").mkdir()
        (tmp_path / "not-a-skill" / "random.txt").write_text("ignore me")

        skill_dir = tmp_path / "real-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: real-skill\ndescription: Real\n---\n\nInstructions.\n"
        )
        skills = load_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "real-skill"

    def test_ignores_files_in_skills_dir(self, tmp_path: Path):
        # A loose .md file at the top level should be skipped (not a directory)
        (tmp_path / "random.md").write_text("Not a skill")
        skills = load_skills(tmp_path)
        assert len(skills) == 0

    def test_returns_empty_list_for_empty_dir(self, tmp_path: Path):
        skills = load_skills(tmp_path)
        assert skills == []

    def test_returns_empty_list_for_missing_dir(self, tmp_path: Path):
        skills = load_skills(tmp_path / "nonexistent")
        assert skills == []

    def test_strips_frontmatter_from_instructions(self, tmp_path: Path):
        skill_dir = tmp_path / "test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n\nThe actual instructions start here.\n"
        )
        skills = load_skills(tmp_path)
        assert "---" not in skills[0].instructions
        assert skills[0].instructions == "The actual instructions start here."

    def test_multiline_instructions(self, tmp_path: Path):
        skill_dir = tmp_path / "test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n\n"
            "# Step 1\nDo this.\n\n# Step 2\nDo that.\n\n# Step 3\nFinish.\n"
        )
        skills = load_skills(tmp_path)
        assert "# Step 1" in skills[0].instructions
        assert "# Step 3" in skills[0].instructions

    def test_preserves_description_with_colons(self, tmp_path: Path):
        """Test that descriptions containing colons are parsed correctly."""
        skill_dir = tmp_path / "test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: test\n"
            'description: "Use this skill when: the user asks for help"\n'
            "---\n\n"
            "Instructions.\n"
        )
        skills = load_skills(tmp_path)
        assert "when:" in skills[0].description


class TestFindSkill:
    """Test finding a skill by name."""

    def test_finds_existing_skill(self):
        skills = [
            Skill(name="alpha", description="A", instructions="a"),
            Skill(name="beta", description="B", instructions="b"),
        ]
        result = find_skill(skills, "beta")
        assert result is not None
        assert result.name == "beta"

    def test_returns_none_for_missing_skill(self):
        skills = [
            Skill(name="alpha", description="A", instructions="a"),
        ]
        result = find_skill(skills, "nonexistent")
        assert result is None

    def test_returns_none_for_empty_list(self):
        result = find_skill([], "anything")
        assert result is None
