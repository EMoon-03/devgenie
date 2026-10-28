# 🧞 DevGenie

**An AI assistant for the boring parts of development, right in your terminal.**

[![Tests](https://github.com/EMoon-03/devgenie/actions/workflows/tests.yml/badge.svg)](https://github.com/EMoon-03/devgenie/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%20%E2%80%93%203.15-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

DevGenie writes commit messages, reviews diffs, drafts changelogs and standups, generates tests and docstrings, turns plain English into shell commands, and explains stack traces.

It runs on a **local model through [Ollama](https://ollama.com) by default**: no API key, no account, and your code never leaves your machine. When you want a bigger model, switch to **OpenAI** or **Anthropic** with one setting.

```console
$ git add .
$ devgenie commit
Generating commit message...

feat(auth): add JWT token validation and refresh

[c]ommit, [r]egenerate, [q]uit: c
Committed successfully!
```

---

## Contents

- [Quick start](#quick-start)
- [Commands](#commands)
- [Choosing a model or provider](#choosing-a-model-or-provider)
- [Large diffs and the context window](#large-diffs-and-the-context-window)
- [How it works](#how-it-works)
- [Adding your own command](#adding-your-own-command)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Quick start

**You need:** Python 3.10 or newer, git, and [Ollama](https://ollama.com/download).

```bash
# 1. Start Ollama and download the default model (one time, ~4.7 GB)
ollama serve
ollama pull llama3

# 2. Install DevGenie
git clone https://github.com/EMoon-03/devgenie.git
cd devgenie
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .

# 3. Try it inside any git repository
cd ~/your-project
git add .
devgenie commit
```

Run `devgenie --help`, or `devgenie <command> --help`, to see every option.

---

## Commands

| Command | What it does |
|---|---|
| [`devgenie commit`](#commit) | Writes a Conventional Commit message for your staged changes |
| [`devgenie review`](#review) | Reviews a diff for bugs, security issues, performance, and clarity |
| [`devgenie changelog`](#changelog) | Drafts a CHANGELOG entry from the commits between two git refs |
| [`devgenie standup`](#standup) | Summarizes your recent commits as a standup update |
| [`devgenie test`](#test) | Generates unit tests for a source file |
| [`devgenie doc`](#doc) | Adds missing docstrings to a source file |
| [`devgenie shell`](#shell) | Turns a plain-English request into a shell command |
| [`devgenie issue`](#issue) | Explains an error or stack trace and suggests a fix |

Every command accepts `--model` / `-m` to use a different model for one run ([details](#choosing-a-model-or-provider)).

### commit

Reads your **staged** changes and proposes a commit message in [Conventional Commits](https://www.conventionalcommits.org/) format. You approve it, ask for another one, or cancel; nothing is committed without your `c`.

```bash
git add src/auth.py
devgenie commit
```

### review

Reviews your **staged** changes by default.

```bash
devgenie review              # staged changes
devgenie review --unstaged   # changes you haven't staged yet
```

Example output:

```text
Reviewing staged changes...

- validate_token() doesn't handle expired tokens; jwt.decode will raise
  ExpiredSignatureError and crash the request.
- Wrap the decode in try/except and return 401 instead.
```

### changelog

```bash
devgenie changelog v1.0.0                    # v1.0.0 up to HEAD
devgenie changelog v1.0.0 v1.1.0             # between two tags
devgenie changelog v1.0.0 --version 1.1.0    # label the entry "1.1.0"
```

Output uses Added / Changed / Fixed / Removed sections, ready to paste into `CHANGELOG.md`.

### standup

```bash
devgenie standup             # commits from the last 24 hours
devgenie standup --hours 8   # last 8 hours
```

### test

```bash
devgenie test src/mymodule.py
```

Prints a complete test file using the usual framework for the language: pytest for Python, Jest for JavaScript/TypeScript, Go's `testing` package, and so on.

### doc

```bash
devgenie doc src/mymodule.py
```

Prints the whole file back with docstrings added wherever they were missing, in the idiomatic style for the language. Supports Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, C#, C, and C++.

> `test` and `doc` print to the terminal and don't change your files, so you can review the output before using it.

### shell

```bash
devgenie shell find all python files modified in the last 3 days
# find . -name "*.py" -mtime -3
```

DevGenie only **prints** the command; it never runs it. Read it before you paste it.

### issue

```bash
devgenie issue "AttributeError: 'NoneType' object has no attribute 'split'"
devgenie issue --file error.log
pytest 2>&1 | devgenie issue        # pipe output straight in
```

You get the likely root cause, where to look, and a suggested fix.

---

## Choosing a model or provider

| Provider | Runs | Needs | Default model |
|---|---|---|---|
| **Ollama** (default) | On your machine | Ollama installed | `llama3` |
| **OpenAI** | In the cloud | `OPENAI_API_KEY` | `gpt-4o-mini` |
| **Anthropic** | In the cloud | `ANTHROPIC_API_KEY` | `claude-sonnet-5-5` |

> **Privacy:** with Ollama, nothing leaves your computer. With OpenAI or Anthropic, your diffs and files are sent to that company's API.

**For one run**, pick a model with `--model`. It applies to whichever provider is active:

```bash
devgenie review --model llama3.1
DEVGENIE_PROVIDER=anthropic devgenie commit
```

**To change the default**, add a config file. DevGenie reads these in order, and later ones win:

1. Built-in defaults
2. Your user config: `~/.config/devgenie/config.toml` (applies to all projects)
3. A project config: `.devgenie.toml` in the folder you run DevGenie from
4. The `DEVGENIE_PROVIDER` environment variable

```toml
# .devgenie.toml
provider = "anthropic"            # "ollama", "openai", or "anthropic"

[ollama]
model = "llama3.1"
max_context = 32768               # see "Large diffs" below

[openai]
model = "gpt-4o"

[anthropic]
model = "claude-sonnet-5-5"
```

Set API keys as environment variables:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

An `api_key` line in a config file also works, but keep keys out of any file you commit to git.

---

## Large diffs and the context window

A model can only read a limited amount of text at once, called its **context window**, measured in tokens (about 3–4 characters of code each).

Ollama's default window is 4,096 tokens on most machines. When a prompt is longer, Ollama doesn't report an error: it **silently throws away the beginning of the prompt**. DevGenie's prompts start with the instructions, so a big diff would lose the instructions and the top of your changes, and you'd get an answer based on part of the input.

DevGenie prevents this by estimating each prompt's size before sending it:

| Prompt size | What DevGenie does |
|---|---|
| Fits in 4,096 tokens | Sends it unchanged |
| Bigger | Asks Ollama for a larger window (8K, 16K or 32K) and prints a note |
| Too big for the model or your limit | Sends nothing and tells you how to fix it |

```text
Error: this request is about 16,235 tokens, but 'llama3' can read at most 8,192 tokens.
Ollama would silently drop the beginning of the prompt (DevGenie's
instructions and the start of your changes), so the answer would be
based on part of the input. Nothing was sent. To fix it:
  - use a model with a longer context, e.g. `--model llama3.1` (128K)
  - or stage/review fewer files at a time
  - or use a cloud provider:  DEVGENIE_PROVIDER=anthropic
```

Bigger windows use more GPU memory and RAM, so DevGenie stops at 32,768 tokens unless you raise `max_context` under `[ollama]`. Note that `llama3` itself can't go past 8,192 tokens; `llama3.1` reads up to 128K.

---

## How it works

```text
 devgenie review
        │
        ▼
 ┌──────────────┐   git diff, git log,   ┌───────────────┐
 │   command    │ ◀── a file, or stdin ──│  your project  │
 └──────┬───────┘                        └───────────────┘
        │ prompt
        ▼
 ┌──────────────┐  picks the provider from config, env, and --model
 │  llm_client  │
 └──────┬───────┘
        ▼
 ┌──────────────────────────────────────────┐
 │  Provider: Ollama │ OpenAI │ Anthropic    │──▶ streams the answer to your terminal
 └──────────────────────────────────────────┘
```

- **Commands don't know which model answers.** Every command calls one function, `stream_response(prompt)`. Providers share a small interface (`Provider.stream`), so adding one means writing a class and registering it, without touching any command.
- **Answers stream as they're written**, so you see output immediately instead of waiting for the full response.
- **No SDKs.** All three providers use plain HTTP via `requests`, which keeps DevGenie down to two dependencies: `click` and `requests` (plus `tomli` on Python 3.10).

```text
src/devgenie/
├── cli.py            # entry point; finds commands automatically
├── commands/         # one file per command (commit.py, review.py, ...)
├── providers/        # ollama.py, openai.py, anthropic.py, base.py
├── llm_client.py     # stream_response(): the one call every command makes
├── config.py         # layered config loading
└── git_utils.py      # git and file helpers (UTF-8 everywhere)
```

---

## Adding your own command

Commands are discovered automatically: add a file to `src/devgenie/commands/` that defines `command`, and it shows up in `devgenie --help`. Nothing else needs editing.

```python
# src/devgenie/commands/explain.py
import click

from .._shared import model_option
from ..git_utils import read_file
from ..llm_client import stream_response


@click.command("explain")
@model_option
@click.argument("filepath")
def command(model, filepath):
    """Explain what a source file does."""
    code = read_file(filepath)
    if code is None:
        click.echo(f"Error: Could not read '{filepath}'")
        return
    stream_response(f"Explain this code:\n\n{code}", model=model)
```

```bash
devgenie explain src/devgenie/cli.py
```

---

## Development

```bash
pip install -e ".[dev]"
pytest
```

The test suite mocks every network call, so it runs offline in under a second and doesn't need Ollama or API keys. GitHub Actions runs it on Python 3.10 through 3.15, on both Linux and Windows.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `Could not connect to Ollama` | Start it with `ollama serve` |
| `Model 'llama3' not found` | Download it with `ollama pull llama3` |
| `this request is about N tokens, but ...` | The input is too big for the model. Stage fewer files, use `--model llama3.1`, or raise `max_context` ([details](#large-diffs-and-the-context-window)) |
| `Missing API key for 'openai'` | `export OPENAI_API_KEY=...` (or `ANTHROPIC_API_KEY`) |
| `Not a git repository` | Run DevGenie from inside a git repo |
| `No staged changes` | Stage files first with `git add` |

---

## License

MIT
