"""FAISS vector store for dense retrieval."""
import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
import structlog

logger = structlog.get_logger()


class FAISSVectorStore:
    """FAISS-backed vector store for knowledge chunk retrieval."""

    def __init__(self, index_path: str, dimension: int = 384):
        self.index_path = index_path
        self.dimension = dimension
        self.index = None
        self.metadata: List[Dict] = []
        self._metadata_path = index_path + "_metadata.json"

    def build(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Build FAISS index from embeddings and metadata."""
        import faiss

        n, d = embeddings.shape
        self.dimension = d
        self.metadata = metadata

        # Use IndexFlatIP for cosine similarity (embeddings should be normalized)
        self.index = faiss.IndexFlatIP(d)
        self.index.add(embeddings.astype(np.float32))
        logger.info("faiss_index_built", vectors=n, dimension=d)

    def save(self):
        """Save index and metadata to disk."""
        import faiss

        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self._metadata_path, "w") as f:
            json.dump(self.metadata, f, default=str)
        logger.info("faiss_index_saved", path=self.index_path, count=len(self.metadata))

    def load(self) -> bool:
        """Load index and metadata from disk."""
        import faiss

        if not os.path.exists(self.index_path) or not os.path.exists(self._metadata_path):
            logger.warning("faiss_index_not_found", path=self.index_path)
            return False
        self.index = faiss.read_index(self.index_path)
        with open(self._metadata_path, "r") as f:
            self.metadata = json.load(f)
        self.dimension = self.index.d
        logger.info("faiss_index_loaded", vectors=self.index.ntotal, dimension=self.dimension)
        return True

    def search(
        self, query_embedding: np.ndarray, top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """Search for nearest neighbors. Returns list of (metadata, score)."""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            results.append((self.metadata[idx], float(score)))
        return results

    @property
    def is_ready(self) -> bool:
        return self.index is not None and self.index.ntotal > 0

    @property
    def count(self) -> int:
        return self.index.ntotal if self.index else 0
