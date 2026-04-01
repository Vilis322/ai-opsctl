"""Tests for RAG endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rag_query_missing_question():
    resp = client.post("/ml/rag/query", json={})
    assert resp.status_code == 422


def test_rag_query_returns_answer():
    mock_pipeline = MagicMock()
    mock_pipeline.query_with_llm.return_value = {
        "answer": "The ROI for Maxwell is 340%.",
        "sources": [{"content": "Maxwell has income $50K...", "score": 0.92}],
    }

    with patch("app.api.rag.get_rag_pipeline", return_value=mock_pipeline):
        resp = client.post("/ml/rag/query", json={
            "question": "What is the ROI for Maxwell?",
            "collection_id": "test-collection",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "sources" in data


def test_rag_collections_list():
    mock_pipeline = MagicMock()
    mock_pipeline.list_collections.return_value = []

    with patch("app.api.rag.get_rag_pipeline", return_value=mock_pipeline):
        resp = client.get("/ml/rag/collections")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
