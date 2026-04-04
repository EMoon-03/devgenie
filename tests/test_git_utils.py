from unittest.mock import MagicMock, patch

from devgenie.git_utils import (
    commit_with_message,
    get_recent_commits,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repo,
)


def _mock_run(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def test_is_git_repo_true():
    with patch("subprocess.run", return_value=_mock_run(stdout="true")):
        assert is_git_repo() is True


def test_is_git_repo_false():
    with patch("subprocess.run", return_value=_mock_run(returncode=128, stderr="not a repo")):
        assert is_git_repo() is False


def test_get_staged_changes_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="")):
        assert get_staged_changes() == ""


def test_get_staged_changes_with_diff():
    with patch("subprocess.run", return_value=_mock_run(stdout="diff --git a/foo.py b/foo.py")):
        result = get_staged_changes()
        assert result is not None
        assert "diff" in result


def test_get_staged_changes_error():
    with patch("subprocess.run", return_value=_mock_run(returncode=1, stderr="fatal")):
        assert get_staged_changes() is None


def test_get_unstaged_changes_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="")):
        assert get_unstaged_changes() == ""


def test_get_recent_commits_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="")):
        assert get_recent_commits() == []


def test_get_recent_commits_with_data():
    with patch("subprocess.run", return_value=_mock_run(stdout="abc1234 feat: add x\ndef5678 fix: bug")):
        result = get_recent_commits()
        assert len(result) == 2
        assert "feat" in result[0]


def test_commit_with_message_success():
    with patch("subprocess.run", return_value=_mock_run(stdout="")):
        assert commit_with_message("feat: add thing") is True


def test_commit_with_message_failure():
    with patch("subprocess.run", return_value=_mock_run(returncode=1, stderr="nothing to commit")):
        assert commit_with_message("feat: add thing") is False
