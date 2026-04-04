import json
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"


def stream_response(prompt: str, model: str = DEFAULT_MODEL) -> str | None:
    """Stream a response from Ollama, printing tokens as they arrive.

    Returns the full response text, or None on error.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt},
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
        if e.response.status_code == 404:
            print(
                f"Error: Model '{model}' not found. Try: ollama pull {model}",
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

    print()  # trailing newline after streaming
    return "".join(tokens).strip()
