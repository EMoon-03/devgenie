import click
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
    from datetime import date

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
