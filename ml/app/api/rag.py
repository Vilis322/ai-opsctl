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
