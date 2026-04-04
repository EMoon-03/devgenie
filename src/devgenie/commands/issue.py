import click
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
