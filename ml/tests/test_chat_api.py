"""Tests for chat inference endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/ml/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_chat_complete_missing_messages():
    resp = client.post("/ml/chat/complete", json={})
    assert resp.status_code == 422


def test_chat_complete_returns_response():
    mock_backend = MagicMock()
    mock_backend.generate.return_value = "This is a test response."

    with patch("app.api.chat.get_inference_backend", return_value=mock_backend):
        resp = client.post("/ml/chat/complete", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert data["content"] == "This is a test response."


def test_chat_stream_returns_sse():
    async def mock_stream(messages, **kwargs):
        for token in ["Hello", " world", "!"]:
            yield token

    mock_backend = MagicMock()
    mock_backend.stream = mock_stream

    with patch("app.api.chat.get_inference_backend", return_value=mock_backend):
        resp = client.post("/ml/chat", json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        })
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
