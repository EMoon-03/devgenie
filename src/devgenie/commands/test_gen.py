import os
import click
from ..git_utils import read_file
from ..llm_client import stream_response

_PROMPT = """\
Generate comprehensive unit tests for the following {language} code.

Rules:
- Cover all public functions and methods
- Include edge cases and error conditions
- Use the standard testing framework for {language} \
(pytest for Python, jest for JS/TS, testing for Go, etc.)
- Output ONLY the test file, no explanation or markdown fences

Code to test:
{code}

Test file:"""

_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".cs": "C#",
}


def run(model: str, filepath: str) -> None:
    ext = os.path.splitext(filepath)[1].lower()
    language = _LANGUAGE_MAP.get(ext, "code")

    code = read_file(filepath)
    if code is None:
        click.echo(f"Error: Could not read '{filepath}'")
        return

    click.echo(f"Generating tests for {filepath} ({language})...\n")
    stream_response(_PROMPT.format(language=language, code=code), model=model)
