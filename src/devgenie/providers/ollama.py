import json
import sys

import requests

from .base import Provider


class OllamaProvider(Provider):
    """Local LLM provider, talking to an Ollama server on this machine.

    DevGenie's default: no API key, no cloud, code never leaves your machine.
    This is the original DevGenie streaming logic, now behind the interface.
    """

    name = "ollama"
    URL = "http://localhost:11434/api/generate"
    DEFAULT_MODEL = "llama3"

    def __init__(self, model: str | None = None):
        super().__init__(model or self.DEFAULT_MODEL)

    def stream(self, prompt: str) -> str | None:
        try:
            response = requests.post(
                self.URL,
                json={"model": self.model, "prompt": prompt},
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print(
                "Error: Could not connect to Ollama. Is it running? Try: ollama serve",
                file=sys.stderr,
            )
            return None
        except requests.exceptions.HTTPError as e:
            if getattr(e, "response", None) is not None and e.response.status_code == 404:
                print(
                    f"Error: Model '{self.model}' not found. Try: ollama pull {self.model}",
                    file=sys.stderr,
                )
            else:
                print(f"Error: {e}", file=sys.stderr)
            return None

        tokens = []
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            token = chunk.get("response", "")
            print(token, end="", flush=True)
            tokens.append(token)
            if chunk.get("done"):
                break

        print()
        return "".join(tokens).strip()
