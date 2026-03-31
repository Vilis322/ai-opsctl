"""MLX inference backend — Apple Silicon native via mlx-lm."""

from typing import AsyncIterator
import asyncio
from .base import InferenceBackend
from ..core.config import settings


class MLXBackend(InferenceBackend):
    """MLX-LM backend for Apple Silicon. Loads model on first use."""

    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.mlx_model
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self):
        if self._model is None:
            from mlx_lm import load
            self._model, self._tokenizer = load(self.model_path)

    def generate(self, messages: list[dict], max_tokens: int = 2048) -> str:
        self._ensure_loaded()
        from mlx_lm import generate

        prompt = self._format_messages(messages)
        response = generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
        )
        return response

    async def stream(self, messages: list[dict], max_tokens: int = 2048) -> AsyncIterator[str]:
        self._ensure_loaded()
        from mlx_lm import stream as mlx_stream

        prompt = self._format_messages(messages)

        def _sync_stream():
            return mlx_stream(
                self._model,
                self._tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
            )

        loop = asyncio.get_event_loop()
        gen = await loop.run_in_executor(None, _sync_stream)

        for chunk in gen:
            yield chunk.text
            await asyncio.sleep(0)

    def is_loaded(self) -> bool:
        return self._model is not None

    def get_model_info(self) -> dict:
        return {
            "backend": "mlx",
            "model": self.model_path,
            "loaded": self.is_loaded(),
        }

    def unload(self):
        """Free model from memory."""
        self._model = None
        self._tokenizer = None

    def _format_messages(self, messages: list[dict]) -> str:
        """Format chat messages into a prompt string for Llama-style models."""
        if self._tokenizer and hasattr(self._tokenizer, "apply_chat_template"):
            return self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

        # Fallback: simple concatenation
        parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                parts.append(f"<|system|>\n{content}")
            elif role == "user":
                parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)
