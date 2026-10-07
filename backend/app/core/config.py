"""ResolveAI Backend Configuration."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Bot-ए-rar"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./resolveai.db"

    # Model
    model_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    model_path: str = "./models/adapters/resolveai-support-v0.1"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # RAG
    faiss_index_path: str = "./data/processed/faiss_index"
    bm25_index_path: str = "./data/processed/bm25_index.pkl"
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Reranker
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_enabled: bool = True

    # Confidence
    confidence_high: int = 80
    confidence_medium: int = 60

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # Security
    secret_key: str = "change-this-to-a-random-secret-key-in-production"
    cors_origins: str = "http://localhost:5173"
    access_token_expire_minutes: int = 480

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Try loading from project root if .env is not in cwd
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_env_file = os.path.join(_project_root, ".env") if os.path.exists(os.path.join(_project_root, ".env")) else ".env"

# Ensure database_url is absolute so seed script and backend use the same file
_default_db_path = os.path.join(_project_root, "resolveai.db")
_default_db_url = f"sqlite:///{_default_db_path}"

settings = Settings(_env_file=_env_file)

# Override relative SQLite URL with absolute path
if settings.database_url == "sqlite:///./resolveai.db":
    settings.database_url = _default_db_url
