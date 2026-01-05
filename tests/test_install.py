import pytest
import json
from pathlib import Path
from taskman import core


def test_install_skills_creates_dir(mock_home):
    """install_skills creates ~/.claude/skills/ if needed"""
    core.install_skills("claude")
    assert (mock_home / ".claude" / "skills" / "taskman").is_dir()


def test_install_skills_copies_all_files(mock_home):
    """install_skills copies all skill .md files"""
    result = core.install_skills("claude")
    skills_dir = mock_home / ".claude" / "skills" / "taskman"

    expected = ["describe.md", "sync.md", "history-diffs.md",
                "history-batch.md", "history-search.md"]
    for skill in expected:
        assert (skills_dir / skill).exists(), f"Missing: {skill}"


def test_install_skills_overwrites_existing(mock_home):
    """install_skills overwrites existing skill files"""
    skills_dir = mock_home / ".claude" / "skills" / "taskman"
    skills_dir.mkdir(parents=True)
    (skills_dir / "describe.md").write_text("old content")

    core.install_skills("claude")

    content = (skills_dir / "describe.md").read_text()
    assert content != "old content"


def test_install_mcp_claude_dot_mcp(mock_home, tmp_path, monkeypatch):
    """install_mcp writes to .mcp.json when it exists"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".mcp.json").write_text("{}")

    result = core.install_mcp("claude")

    config = json.loads((tmp_path / ".mcp.json").read_text())
    assert "mcpServers" in config
    assert "taskman" in config["mcpServers"]


def test_install_mcp_claude_home_fallback(mock_home, tmp_path, monkeypatch):
    """install_mcp falls back to ~/.claude.json"""
    monkeypatch.chdir(tmp_path)
    # No .mcp.json in cwd

    result = core.install_mcp("claude")

    config = json.loads((mock_home / ".claude.json").read_text())
    assert "mcpServers" in config
    assert "taskman" in config["mcpServers"]


def test_install_mcp_cursor(mock_home, tmp_path, monkeypatch):
    """install_mcp writes cursor config"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{}")

    result = core.install_mcp("cursor")

    config = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
    assert "mcpServers" in config


def test_install_mcp_codex(mock_home):
    """install_mcp writes codex config to ~/.codex/config.toml"""
    result = core.install_mcp("codex")

    config_path = mock_home / ".codex" / "config.toml"
    assert config_path.exists()
    content = config_path.read_text()
    assert "taskman" in content
    assert "mcp_servers" in content.lower() or "mcpServers" in content


def test_install_mcp_codex_preserves_existing(mock_home):
    """install_mcp preserves existing codex config entries"""
    config_dir = mock_home / ".codex"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('model = "o3"\n')

    core.install_mcp("codex")

    content = (config_dir / "config.toml").read_text()
    assert 'model = "o3"' in content
    assert "taskman" in content


def test_install_mcp_unknown_agent_raises():
    """install_mcp raises ValueError for unknown agent"""
    with pytest.raises(ValueError, match="Unknown agent"):
        core.install_mcp("unknown-agent")


def test_uninstall_skills(mock_home):
    """uninstall_skills removes skill files"""
    # First install
    core.install_skills("claude")
    skills_dir = mock_home / ".claude" / "skills" / "taskman"
    assert (skills_dir / "describe.md").exists()

    # Then uninstall
    core.uninstall_skills("claude")

    # Skills should be gone
    assert not (skills_dir / "describe.md").exists()


def test_uninstall_mcp_claude(mock_home, tmp_path, monkeypatch):
    """uninstall_mcp removes taskman from config"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".mcp.json").write_text("{}")

    core.install_mcp("claude")
    config = json.loads((tmp_path / ".mcp.json").read_text())
    assert "taskman" in config["mcpServers"]

    core.uninstall_mcp("claude")
    config = json.loads((tmp_path / ".mcp.json").read_text())
    assert "taskman" not in config.get("mcpServers", {})


def test_uninstall_mcp_cursor(mock_home, tmp_path, monkeypatch):
    """uninstall_mcp removes taskman from cursor config"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{}")

    core.install_mcp("cursor")
    core.uninstall_mcp("cursor")

    config = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
    assert "taskman" not in config.get("mcpServers", {})


def test_uninstall_mcp_codex(mock_home):
    """uninstall_mcp removes taskman from codex config"""
    # Install first
    core.install_mcp("codex")
    config_path = mock_home / ".codex" / "config.toml"
    assert "taskman" in config_path.read_text()

    # Uninstall
    core.uninstall_mcp("codex")
    content = config_path.read_text()
    assert "taskman" not in content


def test_uninstall_mcp_codex_preserves_other_config(mock_home):
    """uninstall_mcp preserves other codex config entries"""
    config_dir = mock_home / ".codex"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('model = "o3"\n')

    core.install_mcp("codex")
    core.uninstall_mcp("codex")

    content = (config_dir / "config.toml").read_text()
    assert 'model = "o3"' in content
    assert "taskman" not in content
