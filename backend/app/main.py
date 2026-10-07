"""ResolveAI FastAPI Application."""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.db.database import engine, Base

# Add project root for rag imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = structlog.get_logger()

# ── Global services (initialized at startup) ───────────────────
rag_pipeline = None
llm_service = None
copilot_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    global rag_pipeline, llm_service, copilot_service

    logger.info("starting_resolveai", version=settings.app_version)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Initialize RAG pipeline
    try:
        from rag.vector_store import FAISSVectorStore
        from rag.bm25 import BM25Search
        from rag.retriever import HybridRetriever
        from rag.pipeline import RAGPipeline

        faiss_path = os.path.join(project_root, settings.faiss_index_path)
        bm25_path = os.path.join(project_root, settings.bm25_index_path)

        vector_store = FAISSVectorStore(faiss_path)
        bm25_search = BM25Search(bm25_path)

        # Try loading existing indices
        faiss_loaded = vector_store.load()
        bm25_loaded = bm25_search.load()

        retriever = HybridRetriever(
            vector_store=vector_store,
            bm25_search=bm25_search,
            embedding_model=settings.embedding_model,
            reranker_model=settings.reranker_model,
            reranker_enabled=settings.reranker_enabled,
        )

        rag_pipeline = RAGPipeline(retriever)
        logger.info("rag_pipeline_initialized",
                     faiss_ready=faiss_loaded,
                     bm25_ready=bm25_loaded)
    except Exception as e:
        logger.error("rag_init_failed", error=str(e))

    # Initialize LLM service
    try:
        from app.llm.service import OllamaProvider, FallbackProvider, LLMService

        if settings.model_provider == "ollama":
            provider = OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
            # Check if Ollama is available
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                    if resp.status_code == 200:
                        logger.info("ollama_connected", model=settings.ollama_model)
                    else:
                        raise Exception("Ollama not responding")
            except Exception:
                logger.warning("ollama_unavailable_using_fallback")
                provider = FallbackProvider()
        else:
            provider = FallbackProvider()

        llm_service = LLMService(provider)
        logger.info("llm_service_initialized", provider=settings.model_provider)
    except Exception as e:
        logger.error("llm_init_failed", error=str(e))
        from app.llm.service import FallbackProvider, LLMService
        llm_service = LLMService(FallbackProvider())

    # Initialize Copilot
    if rag_pipeline and llm_service:
        from app.services.copilot import SupportCopilotService
        copilot_service = SupportCopilotService(rag_pipeline, llm_service)
        logger.info("copilot_service_initialized")

    yield

    # Shutdown
    logger.info("shutting_down_resolveai")


app = FastAPI(
    title="Bot-ए-rar",
    description="AI-Powered Customer Support Copilot",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Import and register routes ──────────────────────────────────
from app.api.routes import auth, conversations, drafts, knowledge, analytics, system, organizations

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(system.router, prefix="/api", tags=["System"])


@app.get("/")
async def root():
    return {
        "name": "Bot-ए-rar",
        "version": settings.app_version,
        "description": "AI-Powered Customer Support Copilot",
        "status": "running",
    }
