from abc import ABC, abstractmethod


class Provider(ABC):
    """Common interface every LLM provider implements.

    The rest of DevGenie only ever calls `provider.stream(prompt)` — it never
    knows whether Ollama, OpenAI, or Anthropic is behind it. That decoupling is
    what lets us add providers, or switch the active one, without touching any
    command code.
    """

    name: str = "base"

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def stream(self, prompt: str) -> str | None:
        """Stream a completion for `prompt`, printing tokens as they arrive.

        Returns the full response text, or None on error. Every provider honors
        this same contract so callers can treat them identically.
        """
        raise NotImplementedError
