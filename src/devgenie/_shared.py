import click

from .git_utils import is_git_repo

# Shared --model option used by every command. Defaults to None so it defers to
# the active provider's configured model; pass it to override for one run.
model_option = click.option(
    "--model", "-m",
    default=None,
    help="Override the model for this run (defaults to the active provider's configured model)",
)


def require_git() -> bool:
    if not is_git_repo():
        click.echo("Error: Not a git repository")
        return False
    return True
