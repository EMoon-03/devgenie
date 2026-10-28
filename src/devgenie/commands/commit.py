import click

from .._shared import model_option, require_git
from ..git_utils import get_staged_changes, commit_with_message
from ..llm_client import stream_response

_PROMPT = """\
Analyze the following git diff and generate a single commit message following \
Conventional Commits format.

Format: type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Rules:
- Imperative mood ("add" not "added")
- Description under 72 characters
- Output ONLY the commit message, nothing else

Diff:
{diff}

Commit message:"""


def run(model: str) -> None:
    diff = get_staged_changes()
    if diff is None:
        click.echo("Error: Could not read staged changes")
        return
    if not diff:
        click.echo("No staged changes. Run 'git add' first.")
        return

    click.echo("Generating commit message...\n")
    message = stream_response(_PROMPT.format(diff=diff), model=model)
    if message is None:
        return

    while True:
        option = click.prompt("\n[c]ommit, [r]egenerate, [q]uit")
        if option == "q":
            click.echo("Cancelled")
            break
        elif option == "c":
            if commit_with_message(message):
                click.echo("Committed successfully!")
            else:
                click.echo("Error: Failed to commit")
            break
        elif option == "r":
            click.echo("\nRegenerating...\n")
            message = stream_response(_PROMPT.format(diff=diff), model=model)
            if message is None:
                return
        else:
            click.echo("Invalid option. Enter c, r, or q")


@click.command("commit")
@model_option
def command(model):
    """Generate a commit message from staged changes."""
    if require_git():
        run(model)
