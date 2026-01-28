import subprocess
import sys
import pytest


@pytest.fixture
def e2e_repo(tmp_path):
    """Full repo setup using taskman init"""
    repo = tmp_path / "myproject"
    repo.mkdir()

    result = subprocess.run(
        [sys.executable, "-m", "taskman.cli", "init"],
        cwd=repo, capture_output=True, text=True
    )
    assert result.returncode == 0, f"init failed: {result.stderr}"
    assert (repo / ".agent-files").exists()
    assert (repo / ".agent-files" / ".jj").exists()  # jj repo, not separate .git

    return repo


def test_e2e_full_workflow(e2e_repo):
    """Full workflow: init, edit, describe, history"""
    agent_dir = e2e_repo / ".agent-files"

    # Verify initial structure
    assert (agent_dir / "STATUS.md").exists()
    assert (agent_dir / "LONGTERM_MEM.md").exists()
    assert (agent_dir / "MEDIUMTERM_MEM.md").exists()
    assert (agent_dir / "tasks").is_dir()

    # Make an edit
    (agent_dir / "STATUS.md").write_text("# Status\n\nWorking on: test task\n")

    # Create checkpoint
    result = subprocess.run(
        [sys.executable, "-m", "taskman.cli", "describe", "added test task"],
        cwd=agent_dir, capture_output=True, text=True
    )
    assert result.returncode == 0

    # Query history
    result = subprocess.run(
        [sys.executable, "-m", "taskman.cli", "history-search", "test task"],
        cwd=agent_dir, capture_output=True, text=True
    )
    assert result.returncode == 0
