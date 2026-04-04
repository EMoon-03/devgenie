import platform
import click
from ..llm_client import stream_response

_PROMPT = """\
Convert the following natural language request into a single {os} shell command.

Rules:
- Output ONLY the command, no explanation or markdown
- Prefer standard Unix tools (find, awk, sed, grep, xargs)
- Chain commands with pipes or && when needed

Request: {query}

Command:"""


def run(model: str, query: str) -> None:
    os_name = platform.system()
    click.echo("Generating shell command...\n")
    stream_response(_PROMPT.format(os=os_name, query=query), model=model)
