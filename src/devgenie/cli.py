import importlib
import pkgutil

import click

from . import commands


@click.group()
def main():
    """DevGenie — AI-powered developer assistant.

    \b
    Runs on local LLMs via Ollama by default (no API keys, no cloud), or on
    OpenAI or Anthropic — switch with one line of config. See the README.

    \b
    Workflows are auto-discovered from the commands/ package: drop in a new
    module that defines a `command` and it becomes a subcommand automatically —
    no edits here.
    """


def _discover_commands() -> None:
    """Auto-register every workflow in the commands package.

    Iterates the modules under devgenie.commands, imports each, and adds its
    module-level `command` (a Click command) to the group. This is what makes
    workflows file-based: a new module with a `command` appears as a subcommand
    with no changes to this file.
    """
    for module_info in pkgutil.iter_modules(commands.__path__):
        module = importlib.import_module(f"{commands.__name__}.{module_info.name}")
        cmd = getattr(module, "command", None)
        if isinstance(cmd, click.Command):
            main.add_command(cmd)


_discover_commands()


if __name__ == "__main__":
    main()
