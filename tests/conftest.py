import pytest
import subprocess
from pathlib import Path


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock home directory for install tests"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def jj_repo(tmp_path):
    """Create a temporary jj repo for testing"""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Create bare origin
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True)

    # Clone with jj
    agent_dir = repo / ".agent-files"
    subprocess.run(["jj", "git", "clone", str(bare), str(agent_dir)], check=True)

    # Create initial structure
    (agent_dir / "STATUS.md").write_text("# Status\n")
    (agent_dir / "tasks").mkdir()

    # Initial commit
    subprocess.run(["jj", "describe", "-m", "initial"], cwd=agent_dir, check=True)
    subprocess.run(["jj", "git", "push", "--allow-new"], cwd=agent_dir, check=True)

    return agent_dir
