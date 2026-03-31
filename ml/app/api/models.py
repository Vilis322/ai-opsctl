"""Model management endpoints — list, load, unload."""

from fastapi import APIRouter
from pydantic import BaseModel
from ..api.chat import get_inference_backend
from ..core.config import settings

router = APIRouter(prefix="/ml", tags=["models"])


class LoadModelRequest(BaseModel):
    model: str


@router.get("/models")
async def list_models():
    """List available models and current backend info."""
    backend = get_inference_backend()
    info = backend.get_model_info()

    return {
        "backend": settings.inference_backend,
        "current_model": info,
        "models": {
            "mlx": settings.mlx_model,
            "ollama": settings.ollama_model,
        },
        "adapters_dir": str(settings.models_dir / "adapters"),
    }


@router.post("/models/load")
async def load_model(request: LoadModelRequest):
    """Load a model or switch to a different one."""
    backend = get_inference_backend()

    if hasattr(backend, "unload"):
        backend.unload()

    if hasattr(backend, "model_path"):
        backend.model_path = request.model
    elif hasattr(backend, "model"):
        backend.model = request.model

    return {
        "status": "loaded",
        "model": request.model,
        "info": backend.get_model_info(),
    }


@router.post("/models/unload")
async def unload_model():
    """Unload current model from memory."""
    backend = get_inference_backend()
    if hasattr(backend, "unload"):
        backend.unload()

    return {
        "status": "unloaded",
        "info": backend.get_model_info(),
    }
