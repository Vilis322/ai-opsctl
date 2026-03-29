# Phase 2: FastAPI ML Service — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI ML service with MLX inference (streaming SSE), RAG pipeline (LangChain + ChromaDB), and LoRA fine-tuning orchestration — all endpoints from the spec.

**Architecture:** FastAPI app at :8100 with 4 modules: inference (MLX/Ollama chat), RAG (LangChain + ChromaDB), training (MLX LoRA), models (load/unload). SQLAlchemy for DB reads (training_runs, rag_collections). Async everywhere.

**Tech Stack:** FastAPI, MLX-LM, LangChain, ChromaDB, Sentence-Transformers, SQLAlchemy, SSE (sse-starlette), Python 3.12+

**Spec:** `docs/superpowers/specs/2026-03-29-ai-opsctl-design.md` (sections 3, 8, 10, 11)

---

## File Structure

```
ml/
|-- app/
|   |-- __init__.py
|   |-- main.py                    <- FastAPI app factory, CORS, routes
|   |-- core/
|   |   |-- __init__.py
|   |   |-- config.py              <- Settings (DB URL, model paths, backend detection)
|   |   +-- database.py            <- SQLAlchemy async session for reads
|   |-- api/
|   |   |-- __init__.py
|   |   |-- chat.py                <- POST /ml/chat (SSE), POST /ml/chat/complete
|   |   |-- training.py            <- POST /ml/train, GET /ml/train/:id, POST /ml/train/:id/stop
|   |   |-- rag.py                 <- POST /ml/rag/query, POST /ml/rag/ingest, GET /ml/rag/collections
|   |   +-- models.py              <- GET /ml/models, POST /ml/models/load, POST /ml/models/unload
|   |-- inference/
|   |   |-- __init__.py
|   |   |-- base.py                <- InferenceBackend abstract class
|   |   |-- mlx_backend.py         <- MLX-LM implementation
|   |   +-- ollama_backend.py      <- Ollama HTTP API implementation
|   |-- rag/
|   |   |-- __init__.py
|   |   |-- pipeline.py            <- RAG pipeline: ingest + query
|   |   +-- embeddings.py          <- Sentence-Transformers embedding wrapper
|   +-- training/
|       |-- __init__.py
|       +-- trainer.py             <- MLX LoRA training orchestration
|-- tests/
|   |-- test_generator.py          <- existing (18 tests)
|   |-- test_chat_api.py           <- chat endpoint tests
|   |-- test_rag_api.py            <- RAG endpoint tests
|   |-- test_training_api.py       <- training endpoint tests
|   +-- test_models_api.py         <- models endpoint tests
+-- requirements.txt               <- already exists
```

---

### Task 1: FastAPI App Skeleton + Config

**Files:**
- Create: `ml/app/main.py`
- Create: `ml/app/core/__init__.py`
- Create: `ml/app/core/config.py`
- Create: `ml/app/core/database.py`
- Create: `ml/app/api/__init__.py`

- [ ] **Step 1: Create ml/app/core/config.py**

```python
"""Application settings with platform detection."""

import platform
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://opsctl:opsctl_dev@localhost:5433/ai_opsctl"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # Model paths
    models_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "models"
    datasets_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "datasets"
    chromadb_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "chromadb"

    # Inference backend: auto-detect Apple Silicon
    inference_backend: str = "mlx" if platform.machine() == "arm64" else "ollama"

    # Ollama (fallback)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # MLX
    mlx_model: str = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    mlx_max_tokens: int = 2048

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"

    # Training defaults
    default_lora_rank: int = 8
    default_lora_alpha: int = 16
    default_learning_rate: float = 1e-4
    default_epochs: int = 3

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
```

- [ ] **Step 2: Create ml/app/core/database.py**

```python
"""SQLAlchemy session for reading training_runs, rag_collections, etc."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Create ml/app/main.py**

```python
"""FastAPI ML Service — inference, RAG, training."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OpsCtl AI — ML Service",
    description="Inference, RAG, and training endpoints. All data is 100% synthetic.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ml/health")
async def health():
    return {"ok": True, "service": "ml", "synthetic_data": True}
```

- [ ] **Step 4: Create __init__.py files**

```bash
touch ml/app/core/__init__.py ml/app/api/__init__.py ml/app/inference/__init__.py ml/app/rag/__init__.py ml/app/training/__init__.py
```

- [ ] **Step 5: Install pydantic-settings**

```bash
cd ml && source .venv/bin/activate && pip install pydantic-settings sse-starlette
```

Add to requirements.txt:
```
pydantic-settings==2.*
sse-starlette==2.*
```

- [ ] **Step 6: Test that the app starts**

```bash
cd ml && source .venv/bin/activate
uvicorn app.main:app --port 8100 --reload
```

Verify: `curl http://localhost:8100/ml/health` returns `{"ok":true,"service":"ml","synthetic_data":true}`

Stop the server after verification.

- [ ] **Step 7: Commit**

```bash
git add ml/app/ ml/requirements.txt
git commit -m "feat(ml): FastAPI skeleton — health endpoint, config with platform detection, DB session"
```

---

### Task 2: Inference Backend Abstraction + Ollama Implementation

**Files:**
- Create: `ml/app/inference/base.py`
- Create: `ml/app/inference/ollama_backend.py`
- Create: `ml/tests/test_chat_api.py`

- [ ] **Step 1: Create test file**

```python
# ml/tests/test_chat_api.py
"""Tests for chat inference endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
```

- [ ] **Step 2: Run tests — should fail**

```bash
cd ml && PYTHONPATH=. python -m pytest tests/test_chat_api.py -v
```

- [ ] **Step 3: Create ml/app/inference/base.py**

```python
"""Abstract base class for inference backends."""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class InferenceBackend(ABC):
    """Interface for LLM inference backends (MLX, Ollama)."""

    @abstractmethod
    def generate(self, messages: list[dict], max_tokens: int = 2048) -> str:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], max_tokens: int = 2048) -> AsyncIterator[str]:
        """Stream response tokens."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        ...

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return info about the currently loaded model."""
        ...
```

- [ ] **Step 4: Create ml/app/inference/ollama_backend.py**

```python
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
```

- [ ] **Step 5: Create ml/app/api/chat.py**

```python
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
    role: str  # user, assistant, system
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
```

- [ ] **Step 6: Register router in main.py**

Add to `ml/app/main.py` after the health endpoint:

```python
from app.api.chat import router as chat_router

app.include_router(chat_router)
```

- [ ] **Step 7: Run tests**

```bash
cd ml && PYTHONPATH=. python -m pytest tests/test_chat_api.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add ml/
git commit -m "feat(ml): chat inference — Ollama backend, SSE streaming, /ml/chat + /ml/chat/complete"
```

---

### Task 3: MLX Inference Backend

**Files:**
- Create: `ml/app/inference/mlx_backend.py`

- [ ] **Step 1: Create ml/app/inference/mlx_backend.py**

```python
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

        # Format messages into prompt
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

        # mlx_lm.stream is synchronous generator — wrap in async
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
            await asyncio.sleep(0)  # yield control

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
```

- [ ] **Step 2: Verify MLX import works (Mac only)**

```bash
cd ml && source .venv/bin/activate
python -c "from app.inference.mlx_backend import MLXBackend; print('MLX import OK')"
```

If mlx-lm is not installed: `pip install mlx-lm`

- [ ] **Step 3: Commit**

```bash
git add ml/app/inference/mlx_backend.py
git commit -m "feat(ml): MLX inference backend — Apple Silicon native, lazy model loading, chat template"
```

---

### Task 4: Models Management Endpoints

**Files:**
- Create: `ml/app/api/models.py`
- Create: `ml/tests/test_models_api.py`

- [ ] **Step 1: Create test file**

```python
# ml/tests/test_models_api.py
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
```

- [ ] **Step 2: Create ml/app/api/models.py**

```python
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

    # For MLX: unload current, load new
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
```

- [ ] **Step 3: Register router in main.py**

Add to `ml/app/main.py`:

```python
from app.api.models import router as models_router

app.include_router(models_router)
```

- [ ] **Step 4: Run tests**

```bash
cd ml && PYTHONPATH=. python -m pytest tests/test_models_api.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ml/
git commit -m "feat(ml): model management — /ml/models list, load, unload endpoints"
```

---

### Task 5: RAG Pipeline (LangChain + ChromaDB)

**Files:**
- Create: `ml/app/rag/embeddings.py`
- Create: `ml/app/rag/pipeline.py`
- Create: `ml/app/api/rag.py`
- Create: `ml/tests/test_rag_api.py`

- [ ] **Step 1: Create test file**

```python
# ml/tests/test_rag_api.py
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
    mock_pipeline.query.return_value = {
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
    resp = client.get("/ml/rag/collections")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

- [ ] **Step 2: Create ml/app/rag/embeddings.py**

```python
"""Embedding model wrapper using Sentence-Transformers."""

from sentence_transformers import SentenceTransformer
from ..core.config import settings

_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts).tolist()


def embed_query(query: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(query).tolist()
```

- [ ] **Step 3: Create ml/app/rag/pipeline.py**

```python
"""RAG pipeline — ingest documents into ChromaDB and query with LLM."""

import chromadb
import json
from pathlib import Path
from ..core.config import settings
from .embeddings import embed_texts, embed_query

_chroma_client = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
    return _chroma_client


class RAGPipeline:
    """RAG pipeline: ingest dataset into ChromaDB, query with context retrieval."""

    def __init__(self):
        self.client = get_chroma_client()

    def ingest(self, dataset_id: str, dataset_version: str) -> dict:
        """Ingest a dataset's training data into a ChromaDB collection."""
        collection_name = f"dataset-{dataset_id[:8]}-{dataset_version}"

        # Get or create collection
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"dataset_id": dataset_id, "version": dataset_version},
        )

        # Load training JSONL
        jsonl_path = settings.datasets_dir / dataset_version / "training.jsonl"
        if not jsonl_path.exists():
            return {"error": f"Training data not found: {jsonl_path}", "doc_count": 0}

        documents = []
        metadatas = []
        ids = []

        with open(jsonl_path) as f:
            for i, line in enumerate(f):
                pair = json.loads(line)
                # Store both prompt and completion as searchable document
                doc = f"Q: {pair['prompt']}\nA: {pair['completion']}"
                documents.append(doc)
                metadatas.append({"type": "qa_pair", "index": i})
                ids.append(f"{collection_name}-{i}")

        if documents:
            # Batch embed and add
            embeddings = embed_texts(documents)
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

        return {
            "collection": collection_name,
            "doc_count": len(documents),
            "status": "ready",
        }

    def query(self, question: str, collection_name: str = None, n_results: int = 5) -> dict:
        """Query the RAG pipeline — retrieve relevant docs and format context."""
        if collection_name:
            collection = self.client.get_collection(collection_name)
        else:
            # Use first available collection
            collections = self.client.list_collections()
            if not collections:
                return {"answer": "No collections available. Ingest a dataset first.", "sources": []}
            collection = collections[0]

        query_embedding = embed_query(question)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        sources = []
        context_parts = []
        for i, doc in enumerate(results["documents"][0]):
            score = 1 - results["distances"][0][i] if results["distances"] else None
            sources.append({"content": doc[:200], "score": round(score, 4) if score else None})
            context_parts.append(doc)

        context = "\n\n".join(context_parts)

        return {
            "answer": None,  # To be filled by LLM
            "context": context,
            "sources": sources,
        }

    def query_with_llm(self, question: str, collection_name: str = None) -> dict:
        """Full RAG: retrieve context + generate answer with LLM."""
        retrieval = self.query(question, collection_name)

        if retrieval["answer"]:  # Error case
            return retrieval

        # Build prompt with context
        from ..api.chat import get_inference_backend
        backend = get_inference_backend()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an analytics assistant. Answer questions based on the provided data context. "
                    "All data is synthetic and for demonstration purposes. "
                    "Be specific with numbers and cite the data."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{retrieval['context']}\n\nQuestion: {question}",
            },
        ]

        answer = backend.generate(messages)
        retrieval["answer"] = answer
        return retrieval

    def list_collections(self) -> list[dict]:
        """List all ChromaDB collections."""
        try:
            collections = self.client.list_collections()
            return [
                {
                    "name": c.name,
                    "metadata": c.metadata,
                    "count": c.count(),
                }
                for c in collections
            ]
        except Exception:
            return []


_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
```

- [ ] **Step 4: Create ml/app/api/rag.py**

```python
"""RAG endpoints — query, ingest, list collections."""

from fastapi import APIRouter
from pydantic import BaseModel
from ..rag.pipeline import get_rag_pipeline

router = APIRouter(prefix="/ml", tags=["rag"])


class RAGQueryRequest(BaseModel):
    question: str
    collection_id: str | None = None
    n_results: int = 5


class RAGIngestRequest(BaseModel):
    dataset_id: str
    dataset_version: str


@router.post("/rag/query")
async def rag_query(request: RAGQueryRequest):
    """Query RAG pipeline — retrieve context + generate answer."""
    pipeline = get_rag_pipeline()
    result = pipeline.query_with_llm(
        question=request.question,
        collection_name=request.collection_id,
    )
    return result


@router.post("/rag/ingest")
async def rag_ingest(request: RAGIngestRequest):
    """Ingest a dataset into ChromaDB for RAG."""
    pipeline = get_rag_pipeline()
    result = pipeline.ingest(
        dataset_id=request.dataset_id,
        dataset_version=request.dataset_version,
    )
    return result


@router.get("/rag/collections")
async def rag_collections():
    """List all RAG collections."""
    pipeline = get_rag_pipeline()
    return pipeline.list_collections()
```

- [ ] **Step 5: Register router in main.py**

Add to `ml/app/main.py`:

```python
from app.api.rag import router as rag_router

app.include_router(rag_router)
```

- [ ] **Step 6: Run tests**

```bash
cd ml && PYTHONPATH=. python -m pytest tests/test_rag_api.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add ml/
git commit -m "feat(ml): RAG pipeline — ChromaDB ingest, embedding search, LLM-powered query"
```

---

### Task 6: Training Orchestration

**Files:**
- Create: `ml/app/training/trainer.py`
- Create: `ml/app/api/training.py`
- Create: `ml/tests/test_training_api.py`

- [ ] **Step 1: Create test file**

```python
# ml/tests/test_training_api.py
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
        "status": "pending",
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
```

- [ ] **Step 2: Create ml/app/training/trainer.py**

```python
"""MLX LoRA training orchestration."""

import threading
import time
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
from ..core.config import settings
from ..core.database import SessionLocal
from seeds.buyers import _generate_cuid


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
                text("""
                    INSERT INTO training_runs (id, dataset_id, model_base, adapter_name, hyperparams, status, started_at, created_at)
                    VALUES (:id, :dataset_id, :model_base, :adapter_name, :hyperparams::jsonb, 'RUNNING', NOW(), NOW())
                """),
                {
                    "id": run_id,
                    "dataset_id": dataset_id,
                    "model_base": model,
                    "adapter_name": name,
                    "hyperparams": str(hp).replace("'", '"'),
                },
            )
            session.commit()
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
            # Check if MLX is available
            if settings.inference_backend != "mlx":
                self._update_run(run_id, "FAILED", {"error": "MLX not available on this platform"})
                return

            training_data_path = settings.datasets_dir / dataset_id / "training.jsonl"
            if not training_data_path.exists():
                # Try by version name
                versions = list(settings.datasets_dir.iterdir()) if settings.datasets_dir.exists() else []
                for v in versions:
                    if (v / "training.jsonl").exists():
                        training_data_path = v / "training.jsonl"
                        break

            if not training_data_path.exists():
                self._update_run(run_id, "FAILED", {"error": "Training data not found"})
                return

            adapter_path = settings.models_dir / "adapters" / adapter_name
            adapter_path.mkdir(parents=True, exist_ok=True)

            # MLX LoRA fine-tuning
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
            completed = "NOW()" if status in ("COMPLETED", "FAILED") else "NULL"
            session.execute(
                text(f"""
                    UPDATE training_runs
                    SET status = :status,
                        metrics = :metrics::jsonb,
                        completed_at = {completed}
                    WHERE id = :id
                """),
                {
                    "id": run_id,
                    "status": status,
                    "metrics": str(metrics).replace("'", '"'),
                },
            )
            session.commit()
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
```

- [ ] **Step 3: Create ml/app/api/training.py**

```python
"""Training endpoints — start, status, stop."""

from fastapi import APIRouter
from pydantic import BaseModel
from ..training.trainer import get_trainer

router = APIRouter(prefix="/ml", tags=["training"])


class TrainRequest(BaseModel):
    dataset_id: str
    base_model: str = None
    adapter_name: str = None
    hyperparams: dict = None


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
```

- [ ] **Step 4: Register router in main.py**

Add to `ml/app/main.py`:

```python
from app.api.training import router as training_router

app.include_router(training_router)
```

- [ ] **Step 5: Run tests**

```bash
cd ml && PYTHONPATH=. python -m pytest tests/test_training_api.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add ml/
git commit -m "feat(ml): training orchestration — LoRA fine-tuning, run management, background training"
```

---

### Task 7: E2E Smoke Test — Full ML Service

**Files:** None (integration test)

- [ ] **Step 1: Start infra**

```bash
cd ~/Projects/work/opsctl/ai-opsctl
make infra
```

- [ ] **Step 2: Start ML service**

```bash
cd ml && source .venv/bin/activate
uvicorn app.main:app --port 8100 --reload
```

- [ ] **Step 3: Verify all endpoints respond**

In a separate terminal:

```bash
# Health
curl -s http://localhost:8100/ml/health | python3 -m json.tool

# Models list
curl -s http://localhost:8100/ml/models | python3 -m json.tool

# RAG collections (empty initially)
curl -s http://localhost:8100/ml/rag/collections | python3 -m json.tool

# Chat complete (will fail if no model loaded — that's OK, verify 500 not crash)
curl -s -X POST http://localhost:8100/ml/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"stream":false}' | python3 -m json.tool

# OpenAPI docs
curl -s http://localhost:8100/docs -o /dev/null -w "%{http_code}"
# Expected: 200
```

- [ ] **Step 4: Run all tests (18 seed + new ML tests)**

```bash
cd ml && PYTHONPATH=. python -m pytest tests/ -v
```

Expected: All tests PASS (18 seed + 10 ML = 28 total).

- [ ] **Step 5: Commit final state**

```bash
cd ~/Projects/work/opsctl/ai-opsctl
git add -A
git commit -m "feat: Phase 2 complete — FastAPI ML service with inference, RAG, training endpoints"
git push origin stage
```

---

## Phase 2 Completion Checklist

- [ ] FastAPI starts on :8100 with /ml/health
- [ ] Chat endpoints: /ml/chat (SSE), /ml/chat/complete
- [ ] Inference backends: MLX (Apple Silicon), Ollama (fallback)
- [ ] RAG: /ml/rag/ingest, /ml/rag/query, /ml/rag/collections
- [ ] Training: /ml/train, /ml/train/:id, /ml/train/:id/stop
- [ ] Models: /ml/models, /ml/models/load, /ml/models/unload
- [ ] 28+ tests passing (18 seed + 10 ML)
- [ ] OpenAPI docs at /docs
- [ ] All synthetic data notices in place
