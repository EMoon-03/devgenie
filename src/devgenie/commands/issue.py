import sys

import click

from .._shared import model_option
from ..git_utils import read_file
from ..llm_client import stream_response

_PROMPT = """\
You are a senior software engineer helping debug an issue. Analyze the \
following error or stack trace.

Provide:
1. **Root cause** — what is most likely causing this
2. **Where to look** — specific files, functions, or areas to investigate
3. **Suggested fix** — concrete steps to resolve it

Be specific and actionable. If you need more context, mention what additional \
information would help.

Error / Stack trace:
{error}

Analysis:"""


def run(model: str, error_text: str) -> None:
    click.echo("Analyzing issue...\n")
    stream_response(_PROMPT.format(error=error_text), model=model)


@click.command("issue")
@model_option
@click.argument("error_text", required=False, metavar="ERROR")
@click.option("--file", "-f", "error_file", default=None, help="Read error from a file")
def command(model, error_text, error_file):
    """Analyze an error or stack trace and suggest fixes.

    \b
    Pass the error as an argument, via --file, or pipe it via stdin:
      devgenie issue "AttributeError: 'NoneType' object has no attribute 'split'"
      devgenie issue --file error.log
      cat traceback.txt | devgenie issue
    """
    if error_file:
        text = read_file(error_file)
        if text is None:
            click.echo(f"Error: Could not read '{error_file}'")
            return
    elif error_text:
        text = error_text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        click.echo("Paste your error/stack trace (Ctrl+D when done):\n")
        text = sys.stdin.read()
    run(model, text)
