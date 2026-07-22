import json
import sys

import requests

from .base import Provider


class OpenAIProvider(Provider):
    """Cloud provider using OpenAI's Chat Completions API.

    Raw HTTP (no SDK) to stay dependency-light and consistent with Ollama.
    Parses the Server-Sent Events stream: each `data:` line is a JSON chunk
    whose `choices[0].delta.content` carries the next token.
    """

    name = "openai"
    URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        super().__init__(model or self.DEFAULT_MODEL)
        self.api_key = api_key

    def stream(self, prompt: str) -> str | None:
        try:
            response = requests.post(
                self.URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to OpenAI.", file=sys.stderr)
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error: OpenAI request failed: {e}", file=sys.stderr)
            return None

        tokens = []
        for line in response.iter_lines():
            if not line:
                continue
            text = line.decode("utf-8") if isinstance(line, bytes) else line
            if not text.startswith("data: "):
                continue
            data = text[len("data: "):]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if token:
                print(token, end="", flush=True)
                tokens.append(token)

        print()
        return "".join(tokens).strip()
