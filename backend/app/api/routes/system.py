"""System health and status routes."""
from fastapi import APIRouter
from app.schemas.schemas import SystemHealthResponse
from app.core.config import settings
import os

router = APIRouter()


@router.get("/system/health", response_model=SystemHealthResponse)
async def health_check():
    """Check system component health."""
    result = SystemHealthResponse()

    # Database check
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1" if hasattr(db, 'execute') else None)
        db.close()
        result.database = "connected"
    except Exception:
        try:
            from sqlalchemy import text
            from app.db.database import SessionLocal
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            result.database = "connected"
        except Exception:
            result.database = "disconnected"

    # RAG Index check
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    faiss_path = os.path.join(project_root, settings.faiss_index_path)
    bm25_path = os.path.join(project_root, settings.bm25_index_path)

    if os.path.exists(faiss_path) and os.path.exists(bm25_path):
        result.rag_index = "ready"
    else:
        result.rag_index = "not_built"

    # Embedding model check
    try:
        from rag.embeddings import get_embedding_model
        get_embedding_model(settings.embedding_model)
        result.embedding_model = "ready"
    except Exception:
        result.embedding_model = "not_loaded"

    # LLM check
    try:
        import httpx
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            base_name = settings.ollama_model.split(":")[0]
            if base_name in model_names or any(base_name in n for n in model_names):
                result.llm = "ready"
            else:
                result.llm = f"model_not_found ({settings.ollama_model})"
        else:
            result.llm = "ollama_error"
    except Exception:
        result.llm = "ollama_offline"

    # Model adapter check
    adapter_path = os.path.join(project_root, settings.model_path)
    if os.path.exists(adapter_path):
        result.model_adapter = "loaded"
    else:
        result.model_adapter = "not_found"

    return result
