"""Hybrid retrieval pipeline combining dense + sparse search with reranking."""
import time
from typing import List, Dict, Tuple, Optional
import numpy as np
import structlog

from rag.embeddings import encode_query
from rag.vector_store import FAISSVectorStore
from rag.bm25 import BM25Search
from rag.reranker import rerank

logger = structlog.get_logger()


class HybridRetriever:
    """Combines FAISS dense retrieval + BM25 keyword search with score fusion."""

    def __init__(
        self,
        vector_store: FAISSVectorStore,
        bm25_search: BM25Search,
        embedding_model: str = "all-MiniLM-L6-v2",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        reranker_enabled: bool = True,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        relevance_threshold: float = 0.3,
    ):
        self.vector_store = vector_store
        self.bm25_search = bm25_search
        self.embedding_model = embedding_model
        self.reranker_model = reranker_model
        self.reranker_enabled = reranker_enabled
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.relevance_threshold = relevance_threshold

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        initial_k: int = 20,
    ) -> Dict:
        """
        Full hybrid retrieval pipeline.

        Returns dict with:
            - results: List of (metadata, score) tuples
            - latency_ms: Total retrieval latency
            - dense_count: Number of dense results
            - sparse_count: Number of sparse results
            - reranked: Whether reranking was applied
        """
        start = time.time()

        # Step 1: Dense retrieval via FAISS
        dense_results = []
        if self.vector_store.is_ready:
            query_embedding = encode_query(query, model_name=self.embedding_model)
            dense_results = self.vector_store.search(query_embedding, top_k=initial_k)

        # Step 2: Sparse retrieval via BM25
        sparse_results = []
        if self.bm25_search.is_ready:
            sparse_results = self.bm25_search.search(query, top_k=initial_k)

        # Step 3: Score fusion
        fused = self._fuse_scores(dense_results, sparse_results)

        # Step 4: Deduplicate
        deduped = self._deduplicate(fused)

        # Step 5: Rerank
        reranked = False
        if self.reranker_enabled and deduped:
            try:
                deduped = rerank(
                    query, deduped,
                    model_name=self.reranker_model,
                    top_k=top_k * 2,
                )
                reranked = True
            except Exception as e:
                logger.warning("reranking_skipped", error=str(e))

        # Step 6: Apply relevance threshold
        filtered = [
            (meta, score) for meta, score in deduped
            if score >= self.relevance_threshold
        ]

        # Step 7: Top-K
        final = filtered[:top_k]

        latency = (time.time() - start) * 1000

        return {
            "results": final,
            "latency_ms": round(latency, 2),
            "dense_count": len(dense_results),
            "sparse_count": len(sparse_results),
            "reranked": reranked,
            "total_candidates": len(fused),
        }

    def _fuse_scores(
        self,
        dense_results: List[Tuple[Dict, float]],
        sparse_results: List[Tuple[Dict, float]],
    ) -> List[Tuple[Dict, float]]:
        """Reciprocal Rank Fusion (RRF) for combining dense + sparse."""
        k = 60  # RRF constant

        score_map: Dict[str, Tuple[Dict, float]] = {}

        for rank, (meta, _score) in enumerate(dense_results):
            chunk_id = meta.get("chunk_id", meta.get("doc_id", str(rank)))
            rrf_score = self.dense_weight / (k + rank + 1)
            if chunk_id in score_map:
                score_map[chunk_id] = (meta, score_map[chunk_id][1] + rrf_score)
            else:
                score_map[chunk_id] = (meta, rrf_score)

        for rank, (meta, _score) in enumerate(sparse_results):
            chunk_id = meta.get("chunk_id", meta.get("doc_id", str(rank)))
            rrf_score = self.sparse_weight / (k + rank + 1)
            if chunk_id in score_map:
                score_map[chunk_id] = (meta, score_map[chunk_id][1] + rrf_score)
            else:
                score_map[chunk_id] = (meta, rrf_score)

        # Sort by fused score
        fused = list(score_map.values())
        fused.sort(key=lambda x: x[1], reverse=True)
        return fused

    def _deduplicate(
        self, results: List[Tuple[Dict, float]]
    ) -> List[Tuple[Dict, float]]:
        """Remove duplicate results by document + chunk ID."""
        seen = set()
        deduped = []
        for meta, score in results:
            key = (meta.get("doc_id", ""), meta.get("chunk_id", ""))
            if key not in seen:
                seen.add(key)
                deduped.append((meta, score))
        return deduped

    @property
    def is_ready(self) -> bool:
        return self.vector_store.is_ready or self.bm25_search.is_ready

    def reload(self):
        """Reload indices from disk after re-indexing."""
        self.vector_store.load()
        self.bm25_search.load()
        logger.info("retriever_indices_reloaded",
                     faiss_ready=self.vector_store.is_ready,
                     bm25_ready=self.bm25_search.is_ready)

