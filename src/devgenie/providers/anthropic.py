import json
import sys

import requests

from .base import Provider


class AnthropicProvider(Provider):
    """Cloud provider using Anthropic's Claude Messages API.

    Raw HTTP with SSE streaming. Claude emits typed events; text tokens arrive
    in `content_block_delta` events under `delta.text`, ending with `message_stop`.
    """

    name = "anthropic"
    URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    MAX_TOKENS = 1024

    def __init__(self, model: str | None = None, api_key: str | None = None):
        super().__init__(model or self.DEFAULT_MODEL)
        self.api_key = api_key

    def stream(self, prompt: str) -> str | None:
        try:
            response = requests.post(
                self.URL,
                headers={
                    "x-api-key": self.api_key or "",
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": self.MAX_TOKENS,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to Anthropic.", file=sys.stderr)
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error: Anthropic request failed: {e}", file=sys.stderr)
            return None

        tokens = []
        for line in response.iter_lines():
            if not line:
                continue
            text = line.decode("utf-8") if isinstance(line, bytes) else line
            if not text.startswith("data: "):
                continue
            data = text[len("data: "):]
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            if event_type == "content_block_delta":
                token = event.get("delta", {}).get("text", "")
                if token:
                    print(token, end="", flush=True)
                    tokens.append(token)
            elif event_type == "message_stop":
                break

        print()
        return "".join(tokens).strip()
