from unittest.mock import MagicMock, patch

import pytest

from devgenie.providers import (
    get_provider,
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
)


def _sse_response(lines):
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.iter_lines.return_value = [ln.encode() for ln in lines]
    return mock


def test_factory_returns_ollama_by_default():
    provider = get_provider({"provider": "ollama", "ollama": {"model": "llama3"}})
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3"


def test_factory_model_override_wins():
    provider = get_provider(
        {"provider": "ollama", "ollama": {"model": "llama3"}}, model_override="mistral"
    )
    assert provider.model == "mistral"


def test_factory_builds_openai_with_env_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    provider = get_provider({"provider": "openai", "openai": {"model": "gpt-4o"}})
    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "sk-test"
    assert provider.model == "gpt-4o"


def test_factory_raises_without_cloud_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Missing API key"):
        get_provider({"provider": "anthropic"})


def test_factory_raises_on_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider({"provider": "made-up"})


def test_openai_stream_parses_sse():
    lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":", world"}}]}',
        "data: [DONE]",
        'data: {"choices":[{"delta":{"content":" ignored"}}]}',
    ]
    provider = OpenAIProvider(model="gpt-4o", api_key="sk-test")
    with patch("requests.post", return_value=_sse_response(lines)):
        assert provider.stream("hi") == "Hello, world"


def test_anthropic_stream_parses_sse():
    lines = [
        'data: {"type":"content_block_delta","delta":{"text":"Hi"}}',
        'data: {"type":"content_block_delta","delta":{"text":" there"}}',
        'data: {"type":"message_stop"}',
        'data: {"type":"content_block_delta","delta":{"text":" ignored"}}',
    ]
    provider = AnthropicProvider(model="claude-3-5-sonnet-20241022", api_key="sk-test")
    with patch("requests.post", return_value=_sse_response(lines)):
        assert provider.stream("hi") == "Hi there"


def test_openai_stream_skips_malformed_chunks():
    lines = [
        "data: not-json",
        'data: {"choices":[{"delta":{"content":"ok"}}]}',
        "data: [DONE]",
    ]
    provider = OpenAIProvider(model="gpt-4o", api_key="sk-test")
    with patch("requests.post", return_value=_sse_response(lines)):
        assert provider.stream("hi") == "ok"
