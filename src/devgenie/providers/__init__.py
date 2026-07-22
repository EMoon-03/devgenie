import os

from .base import Provider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider

# Registry mapping a provider name to its implementation.
# Adding a provider = implement Provider and register it here.
_PROVIDERS: dict[str, type[Provider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

# Cloud providers read their key from the environment, never from config files.
_API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def get_provider(config: dict, model_override: str | None = None) -> Provider:
    """Build the active provider from a resolved config dict (the factory).

    Reads `config["provider"]` to pick the implementation, its model (with an
    optional override), and — for cloud providers — the API key from the
    environment. Raises ValueError with a clear message on an unknown provider
    or a missing key.
    """
    name = config.get("provider", "ollama")
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{name}'. Choose from: {', '.join(_PROVIDERS)}"
        )

    settings = config.get(name) or {}
    model = model_override or settings.get("model")
    provider_cls = _PROVIDERS[name]

    if name == "ollama":
        return provider_cls(model=model)

    api_key = os.environ.get(_API_KEY_ENV[name]) or settings.get("api_key")
    if not api_key:
        raise ValueError(
            f"Missing API key for '{name}'. Set {_API_KEY_ENV[name]} in your environment."
        )
    return provider_cls(model=model, api_key=api_key)


__all__ = [
    "Provider",
    "OllamaProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_provider",
]
