import os
import click
from ..git_utils import read_file
from ..llm_client import stream_response

_PROMPT = """\
Add docstrings to every function and class in the following {language} code \
that is missing one.

Rules:
- Use the idiomatic docstring style for {language}
- Be concise but include parameters and return type where present
- Output ONLY the complete updated file, no explanation or markdown fences

Code:
{code}

Updated code:"""

_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
}


def run(model: str, filepath: str) -> None:
    ext = os.path.splitext(filepath)[1].lower()
    language = _LANGUAGE_MAP.get(ext, "code")

    code = read_file(filepath)
    if code is None:
        click.echo(f"Error: Could not read '{filepath}'")
        return

    click.echo(f"Generating docstrings for {filepath} ({language})...\n")
    stream_response(_PROMPT.format(language=language, code=code), model=model)


import click
from .._shared import model_option


@click.command("doc")
@model_option
@click.argument("filepath")
def command(model, filepath):
    """Add docstrings to all undocumented functions in a source file."""
    run(model, filepath)
