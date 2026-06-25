"""Agent Skills — loading and parsing SKILL.md files.

Follows the Agent Skills standard (agentskills.io):
- Skills are directories containing a SKILL.md file
- SKILL.md has YAML frontmatter (name, description, allowed-tools)
- Body contains the instructions for the LLM
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Skill:
    """A loaded Agent Skill.

    Attributes:
        name: Unique identifier (lowercase, hyphens)
        description: What the skill does and when to use it
        instructions: The markdown body — tells the LLM how to perform the task
        allowed_tools: Tools the skill is allowed to use (None = all tools)
    """

    name: str
    description: str
    instructions: str
    allowed_tools: list[str] | None = None


def _parse_skill_file(skill_md_path: Path) -> Skill | None:
    """Parse a single SKILL.md file into a Skill.

    Returns None if the file is invalid or missing required fields.
    """
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Split frontmatter from body
    if not content.startswith("---"):
        return None

    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return None

    frontmatter_str = content[3:end_idx].strip()
    body = content[end_idx + 4 :].strip()

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return None

    if not isinstance(frontmatter, dict):
        return None

    # Required fields
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not name or not description:
        return None

    # Optional: allowed-tools (space-separated string → list)
    allowed_tools_raw = frontmatter.get("allowed-tools")
    allowed_tools: list[str] | None = None
    if isinstance(allowed_tools_raw, str) and allowed_tools_raw.strip():
        allowed_tools = allowed_tools_raw.split()

    return Skill(
        name=name,
        description=description,
        instructions=body,
        allowed_tools=allowed_tools,
    )


def load_skills(skills_dir: Path) -> list[Skill]:
    """Scan a directory for Agent Skills.

    Each skill is a subdirectory containing a SKILL.md file.
    Subdirectories without SKILL.md are ignored.

    Args:
        skills_dir: Path to the skills directory

    Returns:
        List of parsed Skill objects
    """
    if not skills_dir.is_dir():
        return []

    skills: list[Skill] = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        skill = _parse_skill_file(skill_md)
        if skill is not None:
            skills.append(skill)

    return skills


def find_skill(skills: list[Skill], name: str) -> Skill | None:
    """Find a skill by name.

    Args:
        skills: List of skills to search
        name: Skill name to look for

    Returns:
        The matching Skill, or None if not found
    """
    for skill in skills:
        if skill.name == name:
            return skill
    return None
