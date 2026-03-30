"""Ollama inference backend — HTTP API to local Ollama server."""

import httpx
import json
from typing import AsyncIterator
from .base import InferenceBackend
from ..core.config import settings


class OllamaBackend(InferenceBackend):
    """Ollama backend via HTTP API."""

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_url
        self.model = model or settings.ollama_model

    def generate(self, messages: list[dict], max_tokens: int = 2048) -> str:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    async def stream(self, messages: list[dict], max_tokens: int = 2048) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {"num_predict": max_tokens},
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token

    def is_loaded(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                models = resp.json().get("models", [])
                return any(m["name"].startswith(self.model.split(":")[0]) for m in models)
        except Exception:
            return False

    def get_model_info(self) -> dict:
        return {
            "backend": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "loaded": self.is_loaded(),
        }
