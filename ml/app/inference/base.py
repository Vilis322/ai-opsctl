"""Abstract base class for inference backends."""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class InferenceBackend(ABC):
    """Interface for LLM inference backends (MLX, Ollama)."""

    @abstractmethod
    def generate(self, messages: list[dict], max_tokens: int = 2048) -> str:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], max_tokens: int = 2048) -> AsyncIterator[str]:
        """Stream response tokens."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        ...

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return info about the currently loaded model."""
        ...
