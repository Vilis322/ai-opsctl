"""Tests for training endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_start_training_missing_dataset():
    resp = client.post("/ml/train", json={})
    assert resp.status_code == 422


def test_start_training_returns_run_id():
    mock_trainer = MagicMock()
    mock_trainer.start_run.return_value = {
        "run_id": "test-run-123",
        "status": "running",
        "dataset_id": "test-ds",
    }

    with patch("app.api.training.get_trainer", return_value=mock_trainer):
        resp = client.post("/ml/train", json={
            "dataset_id": "test-ds",
            "base_model": "llama-3.1-8b",
        })
    assert resp.status_code == 200
    assert resp.json()["run_id"] == "test-run-123"


def test_get_training_status():
    mock_trainer = MagicMock()
    mock_trainer.get_run_status.return_value = {
        "run_id": "test-run-123",
        "status": "running",
        "metrics": {"loss": 0.5},
    }

    with patch("app.api.training.get_trainer", return_value=mock_trainer):
        resp = client.get("/ml/train/test-run-123")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"
