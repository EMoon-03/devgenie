import click
from ..git_utils import get_recent_commits
from ..llm_client import stream_response

_PROMPT = """\
Based on the following git commits from the last {hours} hour(s), write a \
brief daily standup update.

Format:
**What I did:**
- (2-4 concise bullet points)

**Blockers:**
- (list any, or "None")

Be professional and focus on the work done, not technical implementation details.

Commits:
{commits}

Standup:"""


def run(model: str, hours: int) -> None:
    commits = get_recent_commits(hours=hours)
    if commits is None:
        click.echo("Error: Could not get recent commits")
        return
    if not commits:
        click.echo(f"No commits found in the last {hours} hour(s)")
        return

    click.echo(f"Found {len(commits)} commit(s) in the last {hours}h. Generating standup...\n")
    commit_list = "\n".join(f"- {c}" for c in commits)
    stream_response(_PROMPT.format(hours=hours, commits=commit_list), model=model)


import click
from .._shared import model_option, require_git


@click.command("standup")
@model_option
@click.option("--hours", "-h", default=24, show_default=True, help="Hours of history to scan")
def command(model, hours):
    """Write a daily standup summary from recent commits."""
    if require_git():
        run(model, hours)
