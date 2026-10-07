"""Embedding service using Sentence Transformers."""
import numpy as np
from typing import List, Optional
import structlog

logger = structlog.get_logger()

_model = None
_model_name = None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load or return cached embedding model."""
    global _model, _model_name
    if _model is None or _model_name != model_name:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("loading_embedding_model", model=model_name)
            _model = SentenceTransformer(model_name)
            _model_name = model_name
            logger.info("embedding_model_loaded", model=model_name)
        except Exception as e:
            logger.error("embedding_model_load_failed", error=str(e))
            raise
    return _model


def encode_texts(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
    normalize: bool = True,
) -> np.ndarray:
    """Encode texts into embeddings."""
    model = get_embedding_model(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=normalize,
    )
    return np.array(embeddings, dtype=np.float32)


def encode_query(
    query: str,
    model_name: str = "all-MiniLM-L6-v2",
) -> np.ndarray:
    """Encode a single query into an embedding."""
    return encode_texts([query], model_name=model_name)[0]


def get_embedding_dim(model_name: str = "all-MiniLM-L6-v2") -> int:
    """Return embedding dimensionality."""
    model = get_embedding_model(model_name)
    return model.get_sentence_embedding_dimension()
