import copy
import os
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for 3.9 / 3.10
    import tomli as tomllib

# Layer 1 — built-in defaults. Ollama (local) is default so DevGenie works with
# no API keys. Cloud model names are just defaults; override in a config file.
DEFAULTS = {
    "provider": "ollama",
    "ollama": {"model": "llama3"},
    "openai": {"model": "gpt-4o-mini"},
    "anthropic": {"model": "claude-3-5-sonnet-20241022"},
}

# Layer 2 — user-level config (all your projects).
USER_CONFIG = Path.home() / ".config" / "devgenie" / "config.toml"
# Layer 3 — project-level config (overrides user config for this repo).
PROJECT_CONFIG = Path(".devgenie.toml")


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_file(path: Path) -> dict:
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def load_config() -> dict:
    """Resolve config from all layers, lowest to highest precedence:

      1. built-in DEFAULTS
      2. user config    (~/.config/devgenie/config.toml)
      3. project config (./.devgenie.toml)
      4. environment    (DEVGENIE_PROVIDER)

    Switching providers is one setting: `provider = "openai"` in a config file,
    or `export DEVGENIE_PROVIDER=openai`.
    """
    config = copy.deepcopy(DEFAULTS)
    if USER_CONFIG.exists():
        config = _deep_merge(config, _load_file(USER_CONFIG))
    if PROJECT_CONFIG.exists():
        config = _deep_merge(config, _load_file(PROJECT_CONFIG))

    env_provider = os.environ.get("DEVGENIE_PROVIDER")
    if env_provider:
        config["provider"] = env_provider

    return config
