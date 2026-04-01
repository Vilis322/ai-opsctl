"""Embedding model wrapper using Sentence-Transformers."""

from ..core.config import settings

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(settings.embedding_model)
        except ImportError:
            raise RuntimeError("sentence-transformers not installed. Run: pip install sentence-transformers")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts).tolist()


def embed_query(query: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(query).tolist()
