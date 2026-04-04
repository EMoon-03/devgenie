import json
from unittest.mock import MagicMock, patch

import requests

from devgenie.llm_client import stream_response


def _make_response(chunks: list[dict]) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.iter_lines.return_value = [json.dumps(c).encode() for c in chunks]
    return mock


def test_stream_response_connection_error():
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
        assert stream_response("test") is None


def test_stream_response_model_not_found():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    http_err = requests.exceptions.HTTPError(response=mock_resp)
    mock_resp.raise_for_status.side_effect = http_err

    with patch("requests.post", return_value=mock_resp):
        assert stream_response("test") is None


def test_stream_response_assembles_tokens():
    chunks = [
        {"response": "feat", "done": False},
        {"response": ": add login", "done": True},
    ]
    with patch("requests.post", return_value=_make_response(chunks)):
        result = stream_response("test prompt")
    assert result == "feat: add login"


def test_stream_response_stops_at_done():
    chunks = [
        {"response": "hello", "done": False},
        {"response": " world", "done": True},
        {"response": " ignored", "done": False},  # should not be included
    ]
    with patch("requests.post", return_value=_make_response(chunks)):
        result = stream_response("test")
    assert result == "hello world"
