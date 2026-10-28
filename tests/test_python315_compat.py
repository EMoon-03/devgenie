"""Behavior that must be identical on Python 3.10 through 3.15.

Python 3.15 turns on UTF-8 mode by default (PEP 686). Before 3.15, text I/O used
the locale encoding (cp1252 on most Windows machines), so the same diff could
decode differently, or crash, depending on the Python version. DevGenie now
reads git output and files as UTF-8 explicitly; these tests pin that down.
"""

import shutil
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from devgenie import config
from devgenie.commands import issue
from devgenie.git_utils import ENCODING, get_staged_changes, read_file
from devgenie.providers import AnthropicProvider, get_provider

NON_ASCII = "café ✓ naïve — 日本語"


def test_git_output_is_decoded_as_utf8():
    with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")) as run:
        get_staged_changes()
    kwargs = run.call_args.kwargs
    assert kwargs["encoding"] == ENCODING == "utf-8"
    assert kwargs["errors"] == "replace"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_real_git_diff_with_non_ascii(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run([*git, "init", "-q"], check=True)
    (tmp_path / "notes.txt").write_text(NON_ASCII + "\n", encoding="utf-8")
    subprocess.run([*git, "add", "notes.txt"], check=True)

    diff = get_staged_changes()

    assert diff is not None
    assert NON_ASCII in diff


def test_read_file_reads_utf8(tmp_path):
    path = tmp_path / "source.py"
    path.write_text(f'GREETING = "{NON_ASCII}"\n', encoding="utf-8")
    assert NON_ASCII in read_file(str(path))


def test_read_file_tolerates_invalid_bytes(tmp_path):
    path = tmp_path / "mixed.txt"
    path.write_bytes(b"ok \xff\xfe still ok")
    text = read_file(str(path))
    assert text is not None
    assert text.startswith("ok ") and text.endswith(" still ok")


def test_read_file_missing_returns_none(tmp_path):
    assert read_file(str(tmp_path / "missing.txt")) is None


def test_issue_reads_error_file_as_utf8(tmp_path):
    log = tmp_path / "error.log"
    log.write_text(f"ValueError: {NON_ASCII}\n", encoding="utf-8")
    with patch.object(issue, "stream_response") as stream:
        result = CliRunner().invoke(issue.command, ["--file", str(log)])
    assert result.exit_code == 0
    prompt = stream.call_args.args[0]
    assert NON_ASCII in prompt


def test_issue_reports_unreadable_file(tmp_path):
    result = CliRunner().invoke(issue.command, ["--file", str(tmp_path / "nope.log")])
    assert "Could not read" in result.output


def test_default_anthropic_model_is_not_retired(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "USER_CONFIG", tmp_path / "none-user.toml")
    monkeypatch.setattr(config, "PROJECT_CONFIG", tmp_path / "none-project.toml")
    monkeypatch.setenv("DEVGENIE_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    provider = get_provider(config.load_config())

    assert provider.model == "claude-sonnet-5-5"
    assert AnthropicProvider.DEFAULT_MODEL == "claude-sonnet-5-5"


def test_anthropic_stream_skips_thinking_deltas():
    lines = [
        'data: {"type":"content_block_delta","delta":{"type":"thinking_delta","thinking":"hmm"}}',
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Answer"}}',
        'data: {"type":"message_stop"}',
    ]
    response = MagicMock()
    response.iter_lines.return_value = [line.encode() for line in lines]
    provider = AnthropicProvider(api_key="sk-test")
    with patch("requests.post", return_value=response):
        assert provider.stream("hi") == "Answer"
