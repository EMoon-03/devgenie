import click

from devgenie.cli import main


def test_all_workflows_auto_discovered():
    """Every command module is registered without being hand-wired in cli.py."""
    expected = {"commit", "review", "changelog", "doc", "shell", "test", "standup", "issue"}
    assert expected.issubset(set(main.commands.keys()))


def test_discovered_items_are_click_commands():
    for cmd in main.commands.values():
        assert isinstance(cmd, click.Command)


def test_new_module_would_be_discovered(tmp_path):
    """Dropping a module with a `command` registers it — the core of file-based
    workflow additions. We simulate discovery on a temp package."""
    import importlib
    import pkgutil
    import sys
    import types

    # Build a throwaway package with one command module.
    pkg = types.ModuleType("fake_cmds")
    pkg.__path__ = [str(tmp_path)]
    sys.modules["fake_cmds"] = pkg
    (tmp_path / "explain.py").write_text(
        "import click\n"
        "@click.command('explain')\n"
        "def command():\n"
        "    pass\n",
        encoding="utf-8",
    )

    group = click.Group()
    for info in pkgutil.iter_modules(pkg.__path__):
        module = importlib.import_module(f"fake_cmds.{info.name}")
        cmd = getattr(module, "command", None)
        if isinstance(cmd, click.Command):
            group.add_command(cmd)

    assert "explain" in group.commands
    del sys.modules["fake_cmds"]
