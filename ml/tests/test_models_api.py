"""Tests for models management endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_models():
    resp = client.get("/ml/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "backend" in data
    assert "models" in data


def test_load_model_returns_status():
    mock_backend = MagicMock()
    mock_backend.get_model_info.return_value = {"backend": "ollama", "model": "test", "loaded": True}

    with patch("app.api.models.get_inference_backend", return_value=mock_backend):
        resp = client.post("/ml/models/load", json={"model": "test-model"})
    assert resp.status_code == 200


def test_unload_model():
    mock_backend = MagicMock()
    mock_backend.get_model_info.return_value = {"backend": "ollama", "model": "test", "loaded": False}

    with patch("app.api.models.get_inference_backend", return_value=mock_backend):
        resp = client.post("/ml/models/unload")
    assert resp.status_code == 200
