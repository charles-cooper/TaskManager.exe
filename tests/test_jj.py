import pytest
from pathlib import Path
from taskman.jj import run_jj, find_agent_files_dir


def test_run_jj_returns_tuple():
    """run_jj returns (returncode, stdout, stderr)"""
    code, stdout, stderr = run_jj(["version"], Path.cwd())
    assert code == 0
    assert "jj" in stdout.lower()


def test_run_jj_raises_on_failure():
    """run_jj raises RuntimeError on non-zero exit"""
    with pytest.raises(RuntimeError):
        run_jj(["nonexistent-command"], Path.cwd())


def test_find_agent_files_dir_found(tmp_path):
    """find_agent_files_dir finds .agent-files/ searching upward"""
    agent_dir = tmp_path / ".agent-files"
    agent_dir.mkdir()
    subdir = tmp_path / "a" / "b" / "c"
    subdir.mkdir(parents=True)

    result = find_agent_files_dir(subdir)
    assert result == agent_dir


def test_find_agent_files_dir_not_found(tmp_path):
    """find_agent_files_dir raises FileNotFoundError if not found"""
    with pytest.raises(FileNotFoundError):
        find_agent_files_dir(tmp_path)
