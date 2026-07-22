import click
from ..git_utils import get_staged_changes, get_unstaged_changes
from ..llm_client import stream_response

_PROMPT = """\
You are an expert code reviewer. Review the following git diff and provide \
concise, actionable feedback.

Focus on:
- Bugs or logic errors
- Security vulnerabilities (injection, auth, data exposure)
- Performance issues
- Clarity and maintainability
- Missing edge case handling

Use bullet points. If the code looks good, say so briefly.

Diff:
{diff}

Review:"""


def run(model: str, staged: bool) -> None:
    diff = get_staged_changes() if staged else get_unstaged_changes()
    label = "staged" if staged else "unstaged"

    if diff is None:
        click.echo(f"Error: Could not read {label} changes")
        return
    if not diff:
        click.echo(f"No {label} changes to review.")
        return

    click.echo(f"Reviewing {label} changes...\n")
    stream_response(_PROMPT.format(diff=diff), model=model)


from .._shared import model_option, require_git


@click.command("review")
@model_option
@click.option(
    "--staged/--unstaged",
    default=True,
    help="Review staged (default) or unstaged changes",
)
def command(model, staged):
    """Review code changes for bugs, security issues, and improvements."""
    if require_git():
        run(model, staged)
