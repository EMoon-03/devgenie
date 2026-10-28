import subprocess
from datetime import datetime, timedelta

# Git emits UTF-8. Python 3.15 makes UTF-8 the default text encoding (PEP 686),
# but older versions use the locale encoding (e.g. cp1252 on Windows), which
# crashes on non-ASCII diffs. Being explicit gives identical behavior on every
# supported version and OS; errors="replace" keeps a stray invalid byte in a
# binary-ish diff from aborting the whole command.
ENCODING = "utf-8"


def _run(*args: str) -> tuple[str | None, str | None]:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding=ENCODING,
        errors="replace",
    )
    if result.returncode != 0:
        return None, result.stderr.strip()
    return result.stdout.strip(), None


def is_git_repo() -> bool:
    _, err = _run("rev-parse", "--is-inside-work-tree")
    return err is None


def get_staged_changes() -> str | None:
    out, err = _run("diff", "--cached")
    return None if err else (out or "")


def get_unstaged_changes() -> str | None:
    out, err = _run("diff")
    return None if err else (out or "")


def get_commit_log(base_branch: str = "main") -> list[str] | None:
    out, err = _run("log", f"{base_branch}..HEAD", "--oneline")
    if err:
        return None
    return out.splitlines() if out else []


def get_recent_commits(hours: int = 24) -> list[str] | None:
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    out, err = _run("log", f"--since={since}", "--oneline", "--all")
    if err:
        return None
    return out.splitlines() if out else []


def get_log_between_refs(from_ref: str, to_ref: str = "HEAD") -> list[str] | None:
    out, err = _run("log", f"{from_ref}..{to_ref}", "--oneline")
    if err:
        return None
    return out.splitlines() if out else []


def commit_with_message(message: str) -> bool:
    _, err = _run("commit", "-m", message)
    return err is None


def read_file(path: str) -> str | None:
    """Read a text file as UTF-8, or return None if it can't be read."""
    try:
        with open(path, encoding=ENCODING, errors="replace") as f:
            return f.read()
    except OSError:
        return None
