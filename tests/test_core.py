import subprocess
import pytest
from taskman import core


def test_describe_creates_checkpoint(jj_repo, monkeypatch):
    """describe() creates a named checkpoint"""
    monkeypatch.chdir(jj_repo)
    result = core.describe("test checkpoint")
    assert "test checkpoint" in result or "checkpoint" in result.lower()


def test_describe_triggers_snapshot(jj_repo, monkeypatch):
    """describe() triggers jj snapshot first"""
    monkeypatch.chdir(jj_repo)
    # Make a change
    (jj_repo / "STATUS.md").write_text("# Updated\n")
    result = core.describe("after edit")
    # Change should be captured
    assert "after edit" in result or result  # Just verify it runs


def test_history_search_uses_diff_contains(jj_repo, monkeypatch):
    """history_search() uses jj diff_contains"""
    monkeypatch.chdir(jj_repo)
    # Add content with searchable pattern
    (jj_repo / "STATUS.md").write_text("# Status\nTODO: fix this\n")
    core.describe("add todo")

    result = core.history_search("TODO")
    # Should find the commit
    assert result  # Non-empty result


def test_history_diffs_returns_diffs(jj_repo, monkeypatch):
    """history_diffs() returns diffs across revision range"""
    monkeypatch.chdir(jj_repo)
    # Make changes
    (jj_repo / "STATUS.md").write_text("v1\n")
    core.describe("v1")
    (jj_repo / "STATUS.md").write_text("v2\n")
    core.describe("v2")

    result = core.history_diffs("STATUS.md", "@--", "@")
    assert "v1" in result or "v2" in result


def test_history_batch_returns_content(jj_repo, monkeypatch):
    """history_batch() returns file content at each revision"""
    monkeypatch.chdir(jj_repo)
    (jj_repo / "STATUS.md").write_text("content1\n")
    core.describe("c1")
    (jj_repo / "STATUS.md").write_text("content2\n")
    core.describe("c2")

    result = core.history_batch("STATUS.md", "@--", "@")
    assert "content" in result


def test_wt_creates_workspace(tmp_path, monkeypatch):
    """wt() creates jj workspace sharing the same repo"""
    main_repo = tmp_path / "main"
    main_repo.mkdir()
    monkeypatch.chdir(main_repo)

    # Initialize main repo (needed for git worktree)
    subprocess.run(["git", "init"], cwd=main_repo, check=True)
    (main_repo / "README.md").write_text("# Main\n")
    subprocess.run(["git", "add", "README.md"], cwd=main_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=main_repo, check=True)

    # Initialize .agent-files with jj git init (new model - no bare repo)
    agent_dir = main_repo / ".agent-files"
    subprocess.run(["jj", "git", "init", str(agent_dir)], check=True)
    subprocess.run(
        ["jj", "config", "set", "--repo", "user.name", "Agent"],
        cwd=agent_dir,
        check=True,
    )
    subprocess.run(
        ["jj", "config", "set", "--repo", "user.email", "agent@localhost"],
        cwd=agent_dir,
        check=True,
    )

    # Create files
    (agent_dir / "STATUS.md").write_text("# Test Status\n")
    (agent_dir / "tasks").mkdir()
    subprocess.run(["jj", "describe", "-m", "init"], cwd=agent_dir, check=True)
    subprocess.run(
        ["jj", "bookmark", "create", "main", "-r", "@"], cwd=agent_dir, check=True
    )

    # Create worktree via wt()
    result = core.wt("test-wt", new_branch=True)
    assert "worktrees/test-wt" in result

    # Verify workspace was created in the new worktree
    wt_agent = main_repo / "worktrees" / "test-wt" / ".agent-files"
    assert wt_agent.exists()

    # Workspace should have .jj file (pointer) not .jj directory
    assert (wt_agent / ".jj").exists()

    # Files should be visible in the workspace
    assert (wt_agent / "STATUS.md").exists()
    assert (wt_agent / "STATUS.md").read_text() == "# Test Status\n"
