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
