import sys
import click

from .git_utils import is_git_repo
from .commands import commit, review, changelog, doc, shell, test_gen, standup, issue

_MODEL = click.option(
    "--model", "-m",
    default="llama3",
    show_default=True,
    help="Ollama model to use",
)

def _require_git() -> bool:
    if not is_git_repo():
        click.echo("Error: Not a git repository")
        return False
    return True


@click.group()
def main():
    """DevGenie — AI-powered developer assistant using local LLMs via Ollama.

    \b
    Commands:
      commit    Generate a commit message from staged changes
      review    Review code changes for bugs and issues
      changelog Generate a CHANGELOG entry between two git refs
      doc       Add docstrings to a source file
      shell     Convert plain English to a shell command
      test      Generate unit tests for a source file
      standup   Write a daily standup from recent commits
      issue     Analyze an error or stack trace
    """


@main.command()
@_MODEL
def commit(model):
    """Generate a commit message from staged changes."""
    if _require_git():
        from .commands import commit as _commit
        _commit.run(model)


@main.command()
@_MODEL
@click.option(
    "--staged/--unstaged",
    default=True,
    help="Review staged (default) or unstaged changes",
)
def review(model, staged):
    """Review code changes for bugs, security issues, and improvements."""
    if _require_git():
        from .commands import review as _review
        _review.run(model, staged)


@main.command()
@_MODEL
@click.argument("from_ref")
@click.argument("to_ref", default="HEAD")
@click.option("--version", "-v", default="Unreleased", show_default=True, help="Release version label")
def changelog(model, from_ref, to_ref, version):
    """Generate a CHANGELOG entry between two git refs (tags, branches, commits)."""
    if _require_git():
        from .commands import changelog as _changelog
        _changelog.run(model, from_ref, to_ref, version)


@main.command()
@_MODEL
@click.argument("filepath")
def doc(model, filepath):
    """Add docstrings to all undocumented functions in a source file."""
    from .commands import doc as _doc
    _doc.run(model, filepath)


@main.command()
@_MODEL
@click.argument("query", nargs=-1, required=True)
def shell(model, query):
    """Convert a plain English description into a shell command.

    \b
    Example:
      devgenie shell find all python files modified in the last 3 days
    """
    from .commands import shell as _shell
    _shell.run(model, " ".join(query))


@main.command("test")
@_MODEL
@click.argument("filepath")
def test_cmd(model, filepath):
    """Generate unit tests for a source file."""
    from .commands import test_gen as _test_gen
    _test_gen.run(model, filepath)


@main.command()
@_MODEL
@click.option("--hours", "-h", default=24, show_default=True, help="Hours of history to scan")
def standup(model, hours):
    """Write a daily standup summary from recent commits."""
    if _require_git():
        from .commands import standup as _standup
        _standup.run(model, hours)


@main.command()
@_MODEL
@click.argument("error_text", required=False, metavar="ERROR")
@click.option("--file", "-f", "error_file", default=None, help="Read error from a file")
def issue(model, error_text, error_file):
    """Analyze an error or stack trace and suggest fixes.

    \b
    Pass the error as an argument, via --file, or pipe it via stdin:
      devgenie issue "AttributeError: 'NoneType' object has no attribute 'split'"
      devgenie issue --file error.log
      cat traceback.txt | devgenie issue
    """
    if error_file:
        try:
            with open(error_file) as f:
                text = f.read()
        except OSError:
            click.echo(f"Error: Could not read '{error_file}'")
            return
    elif error_text:
        text = error_text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        click.echo("Paste your error/stack trace (Ctrl+D when done):\n")
        text = sys.stdin.read()

    from .commands import issue as _issue
    _issue.run(model, text)
