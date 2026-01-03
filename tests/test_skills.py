import pytest
from pathlib import Path


def test_skill_files_exist():
    """All skill files exist in skills/"""
    skills_dir = Path(__file__).parent.parent / "skills"

    expected = [
        "describe.md",
        "sync.md",
        "history-diffs.md",
        "history-batch.md",
        "history-search.md",
    ]

    for skill in expected:
        assert (skills_dir / skill).exists(), f"Missing skill: {skill}"


def test_skill_files_have_run_command():
    """Each skill has a 'Run: taskman' command"""
    skills_dir = Path(__file__).parent.parent / "skills"

    for skill_file in skills_dir.glob("*.md"):
        content = skill_file.read_text()
        assert "taskman" in content, f"{skill_file.name} missing taskman command"
