"""Chat inference endpoints — streaming SSE and complete response."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import json

router = APIRouter(prefix="/ml", tags=["chat"])

# Lazy-loaded backend
_backend = None


def get_inference_backend():
    global _backend
    if _backend is None:
        from ..core.config import settings
        if settings.inference_backend == "mlx":
            try:
                from ..inference.mlx_backend import MLXBackend
                _backend = MLXBackend()
            except ImportError:
                from ..inference.ollama_backend import OllamaBackend
                _backend = OllamaBackend()
        else:
            from ..inference.ollama_backend import OllamaBackend
            _backend = OllamaBackend()
    return _backend


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    max_tokens: int = 2048
    stream: bool = True


class ChatResponse(BaseModel):
    content: str
    tokens_out: int | None = None


@router.post("/chat")
async def chat_stream(request: ChatRequest):
    """Chat with streaming SSE response."""
    backend = get_inference_backend()
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def event_generator():
        try:
            async for token in backend.stream(messages, max_tokens=request.max_tokens):
                yield {"data": json.dumps({"token": token})}
            yield {"data": json.dumps({"done": True})}
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.post("/chat/complete", response_model=ChatResponse)
async def chat_complete(request: ChatRequest):
    """Chat with complete (non-streaming) response."""
    backend = get_inference_backend()
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        content = backend.generate(messages, max_tokens=request.max_tokens)
        return ChatResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
