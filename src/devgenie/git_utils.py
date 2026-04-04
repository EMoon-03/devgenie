import subprocess
from datetime import datetime, timedelta


def _run(*args) -> tuple[str | None, str | None]:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
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
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return None
