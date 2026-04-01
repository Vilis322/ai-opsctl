"""RAG pipeline — ingest documents into ChromaDB and query with LLM."""

import chromadb
import json
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

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"dataset_id": dataset_id, "version": dataset_version},
        )

        jsonl_path = settings.datasets_dir / dataset_version / "training.jsonl"
        if not jsonl_path.exists():
            return {"error": f"Training data not found: {jsonl_path}", "doc_count": 0}

        documents = []
        metadatas = []
        ids = []

        with open(jsonl_path) as f:
            for i, line in enumerate(f):
                pair = json.loads(line)
                doc = f"Q: {pair['prompt']}\nA: {pair['completion']}"
                documents.append(doc)
                metadatas.append({"type": "qa_pair", "index": i})
                ids.append(f"{collection_name}-{i}")

        if documents:
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
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                score = 1 - results["distances"][0][i] if results.get("distances") else None
                sources.append({"content": doc[:200], "score": round(score, 4) if score else None})
                context_parts.append(doc)

        context = "\n\n".join(context_parts)

        return {
            "answer": None,
            "context": context,
            "sources": sources,
        }

    def query_with_llm(self, question: str, collection_name: str = None) -> dict:
        """Full RAG: retrieve context + generate answer with LLM."""
        retrieval = self.query(question, collection_name)

        if retrieval.get("answer"):
            return retrieval

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
            result = []
            for c in collections:
                try:
                    count = c.count()
                except Exception:
                    count = 0
                result.append({
                    "name": c.name,
                    "metadata": c.metadata,
                    "count": count,
                })
            return result
        except Exception:
            return []


_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
