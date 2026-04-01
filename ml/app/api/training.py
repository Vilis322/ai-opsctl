"""Training endpoints — start, status, stop."""

from fastapi import APIRouter
from pydantic import BaseModel
from ..training.trainer import get_trainer

router = APIRouter(prefix="/ml", tags=["training"])


class TrainRequest(BaseModel):
    dataset_id: str
    base_model: str | None = None
    adapter_name: str | None = None
    hyperparams: dict | None = None


@router.post("/train")
async def start_training(request: TrainRequest):
    """Start a new LoRA fine-tuning run."""
    trainer = get_trainer()
    result = trainer.start_run(
        dataset_id=request.dataset_id,
        base_model=request.base_model,
        adapter_name=request.adapter_name,
        hyperparams=request.hyperparams,
    )
    return result


@router.get("/train/{run_id}")
async def get_training_status(run_id: str):
    """Get status of a training run."""
    trainer = get_trainer()
    return trainer.get_run_status(run_id)


@router.post("/train/{run_id}/stop")
async def stop_training(run_id: str):
    """Stop an active training run."""
    trainer = get_trainer()
    return trainer.stop_run(run_id)
