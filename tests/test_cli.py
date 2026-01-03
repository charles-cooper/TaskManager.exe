import subprocess
import sys


def test_cli_help():
    """taskman --help works"""
    result = subprocess.run(
        [sys.executable, "-m", "taskman.cli", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "taskman" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_describe(jj_repo):
    """taskman describe works"""
    result = subprocess.run(
        [sys.executable, "-m", "taskman.cli", "describe", "cli test"],
        capture_output=True, text=True, cwd=jj_repo
    )
    assert result.returncode == 0


def test_cli_history_search(jj_repo):
    """taskman history-search works"""
    result = subprocess.run(
        [sys.executable, "-m", "taskman.cli", "history-search", "TODO"],
        capture_output=True, text=True, cwd=jj_repo
    )
    assert result.returncode == 0
