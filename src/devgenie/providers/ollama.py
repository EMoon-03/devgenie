import json
import math
import sys
from dataclasses import dataclass

import requests

from .base import Provider

# --- Context window sizing --------------------------------------------------
#
# An LLM can only read a fixed number of tokens at once: its *context window*.
# Ollama's default window depends on the machine (4,096 tokens unless the GPU
# has ~24 GB+ of memory). When a prompt is longer than the window, Ollama does
# NOT return an error: it keeps the first few tokens, throws away the start of
# the prompt, and answers from the end. DevGenie's prompts put the instructions
# first and the diff after them, so the instructions and the top of the diff
# were the parts silently lost.
#
# The fix: estimate the prompt's size before sending it, ask Ollama for a big
# enough window via the `num_ctx` option, and refuse (with a clear message)
# when even the largest allowed window is too small.

# Rough characters-per-token for code and diffs. Real tokenizers average ~3-4;
# using 3 over-estimates slightly, which errs on the side of a bigger window.
CHARS_PER_TOKEN = 3
# The smallest default window any Ollama server uses. Prompts that fit in it
# are sent unchanged, so small requests behave exactly as before.
DEFAULT_SERVER_CONTEXT = 4096
# Room left in the window for the model's answer.
OUTPUT_RESERVE = 2048
# Upper bound DevGenie will request unless configured otherwise. Every doubling
# of the window costs more GPU/RAM, so this is a safety cap, not a target.
DEFAULT_MAX_CONTEXT = 32768


def estimate_tokens(text: str) -> int:
    """Estimate how many tokens `text` uses. Ollama has no tokenize endpoint."""
    return math.ceil(len(text) / CHARS_PER_TOKEN)


@dataclass(frozen=True)
class ContextPlan:
    needed: int            # estimated prompt tokens + room for the answer
    num_ctx: int | None    # window to request; None = keep the server default
    limit: int             # largest window allowed for this request
    limited_by: str        # "model" or "config": which cap set `limit`

    @property
    def fits(self) -> bool:
        return self.needed <= self.limit


def plan_context(prompt_tokens: int, max_context: int, model_limit: int | None) -> ContextPlan:
    """Decide which context window to request for a prompt of `prompt_tokens`.

    Windows are rounded up to powers of two (8K, 16K, 32K, ...) so repeated
    runs reuse the same size; changing num_ctx makes Ollama reload the model.
    """
    needed = prompt_tokens + OUTPUT_RESERVE
    if model_limit and model_limit < max_context:
        limit, limited_by = model_limit, "model"
    else:
        limit, limited_by = max_context, "config"

    if needed <= DEFAULT_SERVER_CONTEXT:
        return ContextPlan(needed, None, limit, limited_by)

    window = DEFAULT_SERVER_CONTEXT
    while window < needed:
        window *= 2
    return ContextPlan(needed, min(window, limit), limit, limited_by)


class OllamaProvider(Provider):
    """Local LLM provider, talking to an Ollama server on this machine.

    DevGenie's default: no API key, no cloud, code never leaves your machine.
    """

    name = "ollama"
    BASE_URL = "http://localhost:11434"
    URL = f"{BASE_URL}/api/generate"
    SHOW_URL = f"{BASE_URL}/api/show"
    DEFAULT_MODEL = "llama3"

    def __init__(self, model: str | None = None, max_context: int | None = None):
        super().__init__(model or self.DEFAULT_MODEL)
        self.max_context = int(max_context or DEFAULT_MAX_CONTEXT)
        self._model_limit: int | None = None
        self._model_limit_checked = False

    def model_context_limit(self) -> int | None:
        """The longest context the model supports, from Ollama's /api/show.

        Ollama silently caps num_ctx at this value (llama3's is 8,192), so we
        need it to know whether a prompt can really fit. Cached per run; None
        if Ollama doesn't report it.
        """
        if self._model_limit_checked:
            return self._model_limit
        self._model_limit_checked = True
        try:
            response = requests.post(self.SHOW_URL, json={"model": self.model}, timeout=10)
            response.raise_for_status()
            info = response.json().get("model_info") or {}
        except (requests.exceptions.RequestException, ValueError):
            return None
        for key, value in info.items():
            if key.endswith(".context_length") and isinstance(value, int) and value > 0:
                self._model_limit = value
                break
        return self._model_limit

    def _plan(self, prompt: str) -> ContextPlan:
        tokens = estimate_tokens(prompt)
        # Small prompts need no lookup: they fit in every server's default.
        if tokens + OUTPUT_RESERVE <= DEFAULT_SERVER_CONTEXT:
            return plan_context(tokens, self.max_context, None)
        return plan_context(tokens, self.max_context, self.model_context_limit())

    def _explain_too_long(self, plan: ContextPlan) -> None:
        if plan.limited_by == "model":
            cause = f"'{self.model}' can read at most {plan.limit:,} tokens"
            fixes = (
                "  - use a model with a longer context, e.g. `--model llama3.1` (128K)\n"
                "  - or stage/review fewer files at a time"
            )
        else:
            cause = f"your max_context setting is {plan.limit:,} tokens"
            fixes = (
                "  - raise it in .devgenie.toml:  [ollama]  max_context = 65536\n"
                "    (bigger windows use more GPU/RAM)\n"
                "  - or stage/review fewer files at a time"
            )
        print(
            f"Error: this request is about {plan.needed:,} tokens, but {cause}.\n"
            "Ollama would silently drop the beginning of the prompt (DevGenie's\n"
            "instructions and the start of your changes), so the answer would be\n"
            "based on part of the input. Nothing was sent. To fix it:\n"
            f"{fixes}\n"
            "  - or use a cloud provider:  DEVGENIE_PROVIDER=anthropic",
            file=sys.stderr,
        )

    def stream(self, prompt: str) -> str | None:
        plan = self._plan(prompt)
        if not plan.fits:
            self._explain_too_long(plan)
            return None

        payload: dict = {"model": self.model, "prompt": prompt}
        if plan.num_ctx is not None:
            payload["options"] = {"num_ctx": plan.num_ctx}
            print(
                f"Note: large input (~{plan.needed:,} tokens); "
                f"using a {plan.num_ctx:,}-token context window.",
                file=sys.stderr,
            )

        try:
            response = requests.post(self.URL, json=payload, stream=True, timeout=120)
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
