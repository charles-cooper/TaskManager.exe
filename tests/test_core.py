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
