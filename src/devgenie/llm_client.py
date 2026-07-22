import sys

from .config import load_config
from .providers import get_provider


def stream_response(prompt: str, model: str | None = None) -> str | None:
    """Stream a completion for `prompt` from the configured provider.

    Single entry point every command uses. Resolves the active provider
    (Ollama / OpenAI / Anthropic) from layered config, applies an optional model
    override, and delegates to that provider's `stream`. Returns the full text,
    or None on error. Commands don't know which provider answers.
    """
    config = load_config()
    try:
        provider = get_provider(config, model_override=model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return None
    return provider.stream(prompt)
