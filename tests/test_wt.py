"""Tests for worktree management (wt, wt-list, wt-rm, wt-prune)."""
import subprocess
import pytest
from pathlib import Path
from taskman import core


@pytest.fixture
def wt_setup(tmp_path, monkeypatch):
    """Set up a main repo with .agent-files for worktree testing.
    
    Returns (main_repo, agent_files) paths.
    """
    main_repo = tmp_path / "main"
    main_repo.mkdir()
    monkeypatch.chdir(main_repo)

    # Initialize main git repo
    subprocess.run(["git", "init"], cwd=main_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=main_repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=main_repo, check=True, capture_output=True
    )
    (main_repo / "README.md").write_text("# Main\n")
    (main_repo / ".gitignore").write_text(".agent-files/\n")
    subprocess.run(["git", "add", "README.md", ".gitignore"], cwd=main_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=main_repo, check=True, capture_output=True)

    # Initialize .agent-files with jj
    agent_dir = main_repo / ".agent-files"
    subprocess.run(["jj", "git", "init", str(agent_dir)], check=True, capture_output=True)
    subprocess.run(
        ["jj", "config", "set", "--repo", "user.name", "Agent"],
        cwd=agent_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["jj", "config", "set", "--repo", "user.email", "agent@localhost"],
        cwd=agent_dir, check=True, capture_output=True
    )

    # Create files
    (agent_dir / "STATUS.md").write_text("# Test Status\n")
    (agent_dir / "tasks").mkdir()
    subprocess.run(["jj", "describe", "-m", "init"], cwd=agent_dir, check=True, capture_output=True)
    subprocess.run(
        ["jj", "bookmark", "create", "default", "-r", "@"],
        cwd=agent_dir, check=True, capture_output=True
    )
    subprocess.run(["jj", "new"], cwd=agent_dir, check=True, capture_output=True)

    return main_repo, agent_dir


class TestWtList:
    def test_no_worktrees(self, wt_setup, monkeypatch):
        """wt_list returns 'No worktrees found' when none exist."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)
        result = core.wt_list()
        assert result == "No worktrees found"

    def test_lists_worktree(self, wt_setup, monkeypatch):
        """wt_list shows created worktrees."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)

        # Create a worktree
        core.wt("feature-1", new_branch=True)

        result = core.wt_list()
        assert "feature-1" in result
        assert "git:ok" in result
        assert "jj-ws:ok" in result

    def test_detects_orphaned_jj_workspace(self, wt_setup, monkeypatch):
        """wt_list detects jj workspace with missing directory."""
        main_repo, agent_dir = wt_setup
        monkeypatch.chdir(main_repo)

        # Create worktree then delete directory manually
        core.wt("orphan-test", new_branch=True)
        wt_dir = main_repo / "worktrees" / "orphan-test"
        
        # Remove just the .agent-files directory to orphan the jj workspace
        import shutil
        shutil.rmtree(wt_dir / ".agent-files")

        result = core.wt_list()
        assert "orphan-test" in result
        assert "jj-ws:orphaned" in result


class TestWtRm:
    def test_removes_worktree(self, wt_setup, monkeypatch):
        """wt_rm removes worktree, workspace, and auto-merges changes."""
        main_repo, agent_dir = wt_setup
        monkeypatch.chdir(main_repo)

        # Create worktree
        core.wt("to-remove", new_branch=True)
        wt_dir = main_repo / "worktrees" / "to-remove"
        assert wt_dir.exists()

        # Make a change in the worktree's agent-files
        wt_agent = wt_dir / ".agent-files"
        (wt_agent / "NOTES.md").write_text("# Notes from worktree\n")
        # Trigger jj snapshot
        subprocess.run(["jj", "st"], cwd=wt_agent, capture_output=True, check=True)

        # Remove it
        result = core.wt_rm("to-remove")
        assert "Removed git worktree" in result
        assert "Forgot jj workspace" in result
        assert "Merged changes from 'to-remove'" in result

        # Verify git worktree gone
        assert not wt_dir.exists()
        
        # Bookmark should be deleted after clean merge
        proc = subprocess.run(
            ["jj", "bookmark", "list"], cwd=agent_dir,
            capture_output=True, text=True, check=True
        )
        assert "to-remove" not in proc.stdout
        
        # Changes should be in default workspace
        assert (agent_dir / "NOTES.md").exists()

    def test_blocks_removal_from_inside(self, wt_setup, monkeypatch):
        """wt_rm errors when run from inside target worktree."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)

        # Create worktree
        core.wt("current-wt", new_branch=True)
        wt_dir = main_repo / "worktrees" / "current-wt"

        # Try to remove from inside
        monkeypatch.chdir(wt_dir)
        with pytest.raises(ValueError) as exc_info:
            core.wt_rm("current-wt")
        
        assert "Cannot remove current worktree" in str(exc_info.value)
        assert "cd" in str(exc_info.value)  # Should suggest cd command

    def test_blocks_default_removal(self, wt_setup, monkeypatch):
        """wt_rm refuses to remove default workspace."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)

        with pytest.raises(ValueError) as exc_info:
            core.wt_rm("default")
        
        assert "Cannot remove default" in str(exc_info.value)

    def test_force_removes_dirty_worktree(self, wt_setup, monkeypatch):
        """wt_rm --force removes worktree with uncommitted changes."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)

        # Create worktree with changes
        core.wt("dirty-wt", new_branch=True)
        wt_dir = main_repo / "worktrees" / "dirty-wt"
        (wt_dir / "new-file.txt").write_text("uncommitted\n")

        # Without force should fail
        with pytest.raises(ValueError) as exc_info:
            core.wt_rm("dirty-wt")
        assert "uncommitted" in str(exc_info.value).lower() or "force" in str(exc_info.value).lower()

        # With force should succeed
        result = core.wt_rm("dirty-wt", force=True)
        assert "Removed git worktree" in result
        assert not wt_dir.exists()

    def test_handles_partially_cleaned_state(self, wt_setup, monkeypatch):
        """wt_rm handles worktree where git is gone but jj remains."""
        main_repo, agent_dir = wt_setup
        monkeypatch.chdir(main_repo)

        # Create worktree
        core.wt("partial", new_branch=True)
        wt_dir = main_repo / "worktrees" / "partial"

        # Make a change before removing
        wt_agent = wt_dir / ".agent-files"
        (wt_agent / "PARTIAL.md").write_text("# Partial\n")
        # Trigger jj snapshot
        subprocess.run(["jj", "st"], cwd=wt_agent, capture_output=True, check=True)

        # Manually remove git worktree but leave jj workspace
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt_dir)],
            cwd=main_repo, check=True, capture_output=True
        )

        # wt_rm should still clean up jj workspace and merge
        result = core.wt_rm("partial")
        assert "Forgot jj workspace" in result
        assert "Merged changes" in result

    def test_nonexistent_worktree(self, wt_setup, monkeypatch):
        """wt_rm returns 'nothing to clean' for nonexistent worktree."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)

        result = core.wt_rm("does-not-exist")
        assert "Nothing to clean" in result


class TestWtPrune:
    def test_prunes_orphaned_jj_workspace(self, wt_setup, monkeypatch):
        """wt_prune cleans up jj workspace with missing directory."""
        main_repo, agent_dir = wt_setup
        monkeypatch.chdir(main_repo)

        # Create worktree then delete directory manually (simulating rm -rf)
        core.wt("orphan", new_branch=True)
        wt_dir = main_repo / "worktrees" / "orphan"
        
        import shutil
        shutil.rmtree(wt_dir)

        # Verify orphaned state before prune
        list_result = core.wt_list()
        assert "orphan" in list_result
        assert "orphaned" in list_result

        # Prune should clean it up
        result = core.wt_prune()
        assert "orphan" in result
        assert "Forgot" in result or "git:" in result

        # Should be clean now
        list_after = core.wt_list()
        assert "orphan" not in list_after or "No worktrees" in list_after

    def test_no_orphans(self, wt_setup, monkeypatch):
        """wt_prune reports no orphans when state is clean."""
        main_repo, _ = wt_setup
        monkeypatch.chdir(main_repo)

        result = core.wt_prune()
        assert "No orphaned state" in result
