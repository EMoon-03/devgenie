# DevGenie

All-in-one AI-powered developer assistant that runs entirely on your machine using [Ollama](https://ollama.com). No API keys, no cloud — the code stays local.

## Commands

| Command | What it does |
|---|---|
| `devgenie commit` | Analyzes staged changes and generates a Conventional Commit message |
| `devgenie review` | Reviews your diff for bugs, security issues, and code quality |
| `devgenie changelog <from> <to>` | Generates a CHANGELOG entry between two git refs |
| `devgenie doc <file>` | Adds docstrings to all undocumented functions in a source file |
| `devgenie shell <query>` | Converts plain English into a shell command |
| `devgenie test <file>` | Generates unit tests for a source file |
| `devgenie standup` | Writes a daily standup summary from recent commits |
| `devgenie issue <error>` | Analyzes an error or stack trace and suggests fixes |

## Demo

```bash
# Generate a commit message from staged changes
$ git add .
$ devgenie commit

Generating commit message...
feat(auth): add JWT token validation and refresh mechanism

[c]ommit, [r]egenerate, [q]uit: c
Committed successfully!

# Review your changes before pushing
$ devgenie review

Reviewing staged changes...
- `validate_token()` does not handle expired tokens — will raise uncaught exception
- Consider adding a `try/except` around the JWT decode call

# Turn plain English into a shell command
$ devgenie shell find all python files modified in the last 3 days

Generating shell command...
find . -name "*.py" -mtime -3

# Generate a standup from today's commits
$ devgenie standup

**What I did:**
- Added JWT authentication with token refresh support
- Fixed session expiry handling in the login flow

**Blockers:**
- None
```

## Prerequisites

1. **Python 3.9+**
2. **Ollama** — [install from ollama.com](https://ollama.com)
3. **llama3 model**

```bash
# Install and start Ollama
ollama serve

# Pull the default model
ollama pull llama3
```

## Installation

```bash
git clone https://github.com/EMoon-03/devgenie.git
cd devgenie
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

### Commit messages

```bash
git add .
devgenie commit
# [c]ommit, [r]egenerate, [q]uit
```

### Code review

```bash
devgenie review              # review staged changes (default)
devgenie review --unstaged   # review unstaged changes
```

### Changelog

```bash
devgenie changelog v1.0.0 v1.1.0
devgenie changelog v1.0.0 HEAD --version 1.1.0
```

### Add docstrings

```bash
devgenie doc src/mymodule.py
```

Outputs the full updated file with docstrings added. Supports Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, and C#.

### Shell command generation

```bash
devgenie shell list all docker containers using more than 500mb of memory
devgenie shell recursively delete all __pycache__ folders
```

### Generate tests

```bash
devgenie test src/mymodule.py
```

Outputs a ready-to-use test file using the standard framework for the detected language (pytest, jest, Go testing, etc.).

### Daily standup

```bash
devgenie standup             # last 24 hours (default)
devgenie standup --hours 8   # last 8 hours
```

### Issue / stack trace analysis

```bash
# Pass error inline
devgenie issue "AttributeError: 'NoneType' object has no attribute 'split'"

# Read from a file
devgenie issue --file error.log

# Pipe from stdin
cat traceback.txt | devgenie issue
```

## Options

Every command accepts `--model` / `-m` to switch the Ollama model:

```bash
devgenie commit --model mistral
devgenie review -m codellama
```

## How it works

1. DevGenie reads the relevant context (git diff, commit log, source file, or error text)
2. Builds a focused prompt and sends it to Ollama running locally on `localhost:11434`
3. Streams the response token-by-token so you see output immediately

## Troubleshooting

**`Could not connect to Ollama`**
```bash
ollama serve
```

**`Model not found`**
```bash
ollama pull llama3
```

**`Not a git repository`** — run from inside a git repo, or run `git init` first.

## License

MIT
