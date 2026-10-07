"""Cross-encoder reranker for retrieved results."""
from typing import List, Dict, Tuple, Optional
import structlog

logger = structlog.get_logger()

_reranker = None
_reranker_name = None


def get_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
    """Load or return cached reranker model."""
    global _reranker, _reranker_name
    if _reranker is None or _reranker_name != model_name:
        try:
            from sentence_transformers import CrossEncoder
            logger.info("loading_reranker", model=model_name)
            _reranker = CrossEncoder(model_name)
            _reranker_name = model_name
            logger.info("reranker_loaded", model=model_name)
        except Exception as e:
            logger.error("reranker_load_failed", error=str(e))
            raise
    return _reranker


def rerank(
    query: str,
    results: List[Tuple[Dict, float]],
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    top_k: int = 5,
) -> List[Tuple[Dict, float]]:
    """Rerank results using cross-encoder. Returns reranked (metadata, score) list."""
    if not results:
        return []

    try:
        reranker = get_reranker(model_name)
        pairs = [(query, r[0].get("content", r[0].get("text", ""))) for r in results]
        scores = reranker.predict(pairs)

        # Combine with metadata
        reranked = []
        for i, score in enumerate(scores):
            reranked.append((results[i][0], float(score)))

        # Sort by reranker score descending
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:top_k]

    except Exception as e:
        logger.warning("reranking_failed_using_original", error=str(e))
        # Fallback: return original results sorted by score
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
