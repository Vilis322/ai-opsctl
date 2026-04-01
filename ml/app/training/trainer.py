"""MLX LoRA training orchestration."""

import threading
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
from ..core.config import settings
from ..core.database import SessionLocal


def _generate_cuid() -> str:
    import random
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "c" + "".join(random.choices(chars, k=24))


class Trainer:
    """Manages LoRA fine-tuning runs."""

    def __init__(self):
        self._active_run: dict | None = None
        self._thread: threading.Thread | None = None

    def start_run(
        self,
        dataset_id: str,
        base_model: str = None,
        adapter_name: str = None,
        hyperparams: dict = None,
    ) -> dict:
        """Start a new training run."""
        if self._active_run and self._active_run.get("status") == "running":
            return {"error": "A training run is already active", "run_id": self._active_run["run_id"]}

        run_id = _generate_cuid()
        hp = {
            "learning_rate": settings.default_learning_rate,
            "epochs": settings.default_epochs,
            "lora_rank": settings.default_lora_rank,
            "lora_alpha": settings.default_lora_alpha,
            **(hyperparams or {}),
        }

        model = base_model or settings.mlx_model
        name = adapter_name or f"{dataset_id[:8]}-{datetime.now().strftime('%Y%m%d-%H%M')}"

        # Write to DB
        session = SessionLocal()
        try:
            session.execute(
                text(
                    "INSERT INTO training_runs (id, dataset_id, model_base, adapter_name, hyperparams, status, started_at, created_at) "
                    "VALUES (:id, :dataset_id, :model_base, :adapter_name, cast(:hyperparams as jsonb), 'RUNNING', NOW(), NOW())"
                ),
                {
                    "id": run_id,
                    "dataset_id": dataset_id,
                    "model_base": model,
                    "adapter_name": name,
                    "hyperparams": json.dumps(hp),
                },
            )
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        self._active_run = {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "model_base": model,
            "adapter_name": name,
            "hyperparams": hp,
            "status": "running",
            "metrics": {},
            "started_at": datetime.now().isoformat(),
        }

        # Start training in background thread
        self._thread = threading.Thread(
            target=self._train,
            args=(run_id, dataset_id, model, name, hp),
            daemon=True,
        )
        self._thread.start()

        return {
            "run_id": run_id,
            "status": "running",
            "dataset_id": dataset_id,
            "model_base": model,
            "adapter_name": name,
            "hyperparams": hp,
        }

    def _train(self, run_id: str, dataset_id: str, model: str, adapter_name: str, hp: dict):
        """Background training thread."""
        try:
            if settings.inference_backend != "mlx":
                self._update_run(run_id, "FAILED", {"error": "MLX not available on this platform"})
                return

            # Find training data
            training_data_path = None
            if settings.datasets_dir.exists():
                for v_dir in settings.datasets_dir.iterdir():
                    candidate = v_dir / "training.jsonl"
                    if candidate.exists():
                        training_data_path = candidate
                        break

            if not training_data_path:
                self._update_run(run_id, "FAILED", {"error": "Training data not found"})
                return

            adapter_path = settings.models_dir / "adapters" / adapter_name
            adapter_path.mkdir(parents=True, exist_ok=True)

            from mlx_lm import lora

            lora.train(
                model=model,
                train_data=str(training_data_path),
                adapter_path=str(adapter_path),
                learning_rate=hp["learning_rate"],
                num_epochs=hp["epochs"],
                lora_rank=hp["lora_rank"],
            )

            self._update_run(run_id, "COMPLETED", {"adapter_path": str(adapter_path)})

        except Exception as e:
            self._update_run(run_id, "FAILED", {"error": str(e)})

    def _update_run(self, run_id: str, status: str, metrics: dict):
        """Update training run in DB."""
        session = SessionLocal()
        try:
            completed_clause = ", completed_at = NOW()" if status in ("COMPLETED", "FAILED") else ""
            session.execute(
                text(
                    f"UPDATE training_runs SET status = :status, metrics = cast(:metrics as jsonb){completed_clause} WHERE id = :id"
                ),
                {
                    "id": run_id,
                    "status": status,
                    "metrics": json.dumps(metrics),
                },
            )
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        if self._active_run and self._active_run["run_id"] == run_id:
            self._active_run["status"] = status.lower()
            self._active_run["metrics"] = metrics

    def get_run_status(self, run_id: str) -> dict:
        """Get status of a training run."""
        if self._active_run and self._active_run["run_id"] == run_id:
            return self._active_run

        session = SessionLocal()
        try:
            result = session.execute(
                text("SELECT * FROM training_runs WHERE id = :id"),
                {"id": run_id},
            ).mappings().first()

            if not result:
                return {"error": "Run not found", "run_id": run_id}

            return dict(result)
        finally:
            session.close()

    def stop_run(self, run_id: str) -> dict:
        """Stop an active training run."""
        if self._active_run and self._active_run["run_id"] == run_id:
            self._active_run["status"] = "failed"
            self._update_run(run_id, "FAILED", {"error": "Stopped by user"})
            return {"status": "stopped", "run_id": run_id}
        return {"error": "Run not active", "run_id": run_id}


_trainer = None


def get_trainer() -> Trainer:
    global _trainer
    if _trainer is None:
        _trainer = Trainer()
    return _trainer
