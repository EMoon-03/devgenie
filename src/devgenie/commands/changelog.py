from datetime import date

import click

from .._shared import model_option, require_git
from ..git_utils import get_log_between_refs
from ..llm_client import stream_response

_PROMPT = """\
Generate a CHANGELOG.md entry for the following git commits.

Use this markdown format (omit sections with no relevant commits):
## [{version}] - {date}
### Added
### Changed
### Fixed
### Removed

Commits:
{commits}

CHANGELOG entry:"""


def run(model: str, from_ref: str, to_ref: str, version: str) -> None:
    commits = get_log_between_refs(from_ref, to_ref)
    if commits is None:
        click.echo(f"Error: Could not get commits between '{from_ref}' and '{to_ref}'")
        return
    if not commits:
        click.echo(f"No commits found between {from_ref} and {to_ref}")
        return

    click.echo(f"Found {len(commits)} commits. Generating changelog...\n")
    commit_list = "\n".join(f"- {c}" for c in commits)
    prompt = _PROMPT.format(
        version=version,
        date=date.today().isoformat(),
        commits=commit_list,
    )
    stream_response(prompt, model=model)


@click.command("changelog")
@model_option
@click.argument("from_ref")
@click.argument("to_ref", default="HEAD")
@click.option("--version", "-v", default="Unreleased", show_default=True, help="Release version label")
def command(model, from_ref, to_ref, version):
    """Generate a CHANGELOG entry between two git refs (tags, branches, commits)."""
    if require_git():
        run(model, from_ref, to_ref, version)
