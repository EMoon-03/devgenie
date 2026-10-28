"""Ollama context-window sizing: no more silent truncation of long prompts."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from devgenie.providers import get_provider
from devgenie.providers.ollama import (
    CHARS_PER_TOKEN,
    DEFAULT_MAX_CONTEXT,
    OUTPUT_RESERVE,
    OllamaProvider,
    estimate_tokens,
    plan_context,
)


def _prompt_of(tokens: int) -> str:
    return "x" * (tokens * CHARS_PER_TOKEN)


def _generate_response(text="ok"):
    mock = MagicMock()
    mock.iter_lines.return_value = [json.dumps({"response": text, "done": True}).encode()]
    return mock


def _show_response(context_length):
    mock = MagicMock()
    mock.json.return_value = {"model_info": {"llama.context_length": context_length}}
    return mock


def _fake_ollama(context_length=8192):
    """requests.post stand-in that answers /api/show and /api/generate."""
    calls = []

    def post(url, json=None, **kwargs):
        calls.append((url, json))
        if url == OllamaProvider.SHOW_URL:
            return _show_response(context_length)
        return _generate_response()

    return post, calls


# --- plan_context: the decision, as a pure function -------------------------

def test_estimate_tokens_rounds_up():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abc") == 1
    assert estimate_tokens("abcd") == 2


def test_small_prompt_keeps_server_default():
    plan = plan_context(500, max_context=32768, model_limit=None)
    assert plan.num_ctx is None
    assert plan.fits


def test_large_prompt_rounds_up_to_power_of_two():
    plan = plan_context(6000, max_context=32768, model_limit=None)
    assert plan.needed == 6000 + OUTPUT_RESERVE
    assert plan.num_ctx == 8192
    assert plan.fits


def test_window_is_capped_by_model_limit():
    plan = plan_context(5000, max_context=32768, model_limit=8192)
    assert plan.num_ctx == 8192
    assert plan.limited_by == "model"
    assert plan.fits


def test_too_long_for_model():
    plan = plan_context(20000, max_context=32768, model_limit=8192)
    assert not plan.fits
    assert plan.limit == 8192
    assert plan.limited_by == "model"


def test_too_long_for_config():
    plan = plan_context(40000, max_context=32768, model_limit=131072)
    assert not plan.fits
    assert plan.limited_by == "config"


def test_bucket_larger_than_limit_uses_limit():
    # needs ~10.2K -> next power of two is 16K, but the model stops at 12K
    plan = plan_context(8200, max_context=32768, model_limit=12288)
    assert plan.num_ctx == 12288
    assert plan.fits


# --- OllamaProvider.stream: what actually gets sent --------------------------

def test_small_prompt_sends_no_options_and_skips_show():
    post, calls = _fake_ollama()
    with patch("requests.post", side_effect=post):
        assert OllamaProvider().stream("short prompt") == "ok"
    assert [url for url, _ in calls] == [OllamaProvider.URL]
    assert "options" not in calls[0][1]


def test_large_prompt_requests_bigger_window(capsys):
    post, calls = _fake_ollama(context_length=131072)
    with patch("requests.post", side_effect=post):
        assert OllamaProvider(model="llama3.1").stream(_prompt_of(10000)) == "ok"
    url, payload = calls[-1]
    assert url == OllamaProvider.URL
    assert payload["options"] == {"num_ctx": 16384}
    assert "16,384-token context window" in capsys.readouterr().err


def test_prompt_too_long_is_not_sent(capsys):
    post, calls = _fake_ollama(context_length=8192)
    with patch("requests.post", side_effect=post):
        assert OllamaProvider(model="llama3").stream(_prompt_of(20000)) is None
    assert OllamaProvider.URL not in [url for url, _ in calls]
    err = capsys.readouterr().err
    assert "can read at most 8,192 tokens" in err
    assert "Nothing was sent" in err


def test_model_limit_is_looked_up_once():
    post, calls = _fake_ollama(context_length=131072)
    provider = OllamaProvider()
    with patch("requests.post", side_effect=post):
        provider.stream(_prompt_of(6000))
        provider.stream(_prompt_of(6000))
    assert [url for url, _ in calls].count(OllamaProvider.SHOW_URL) == 1


def test_unknown_model_limit_falls_back_to_max_context():
    def post(url, json=None, **kwargs):
        if url == OllamaProvider.SHOW_URL:
            raise requests.exceptions.ConnectionError
        return _generate_response()

    with patch("requests.post", side_effect=post) as mock_post:
        assert OllamaProvider().stream(_prompt_of(6000)) == "ok"
    payload = mock_post.call_args.kwargs["json"]
    assert payload["options"] == {"num_ctx": 8192}


# --- configuration ------------------------------------------------------------

def test_max_context_comes_from_config():
    provider = get_provider({"provider": "ollama", "ollama": {"max_context": 65536}})
    assert provider.max_context == 65536


def test_max_context_default():
    provider = get_provider({"provider": "ollama", "ollama": {}})
    assert provider.max_context == DEFAULT_MAX_CONTEXT


@pytest.mark.parametrize("tokens", [100, 2000])
def test_existing_small_prompts_unchanged(tokens):
    post, calls = _fake_ollama()
    with patch("requests.post", side_effect=post):
        OllamaProvider().stream(_prompt_of(tokens))
    assert calls[0][1] == {"model": "llama3", "prompt": _prompt_of(tokens)}
