"""BM25 keyword search for sparse retrieval."""
import os
import pickle
import re
from typing import List, Dict, Tuple, Optional
import structlog

logger = structlog.get_logger()


class BM25Search:
    """BM25-based keyword retrieval for knowledge chunks."""

    def __init__(self, index_path: str):
        self.index_path = index_path
        self.bm25 = None
        self.metadata: List[Dict] = []
        self.corpus: List[List[str]] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple whitespace + lowercasing tokenizer."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        tokens = text.split()
        # Remove very short tokens
        return [t for t in tokens if len(t) > 1]

    def build(self, texts: List[str], metadata: List[Dict]):
        """Build BM25 index from texts."""
        from rank_bm25 import BM25Okapi

        self.metadata = metadata
        self.corpus = [self.tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(self.corpus)
        logger.info("bm25_index_built", documents=len(texts))

    def save(self):
        """Save BM25 index to disk."""
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        data = {
            "corpus": self.corpus,
            "metadata": self.metadata,
        }
        with open(self.index_path, "wb") as f:
            pickle.dump(data, f)
        logger.info("bm25_index_saved", path=self.index_path)

    def load(self) -> bool:
        """Load BM25 index from disk."""
        if not os.path.exists(self.index_path):
            logger.warning("bm25_index_not_found", path=self.index_path)
            return False
        from rank_bm25 import BM25Okapi

        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
        self.corpus = data["corpus"]
        self.metadata = data["metadata"]
        self.bm25 = BM25Okapi(self.corpus)
        logger.info("bm25_index_loaded", documents=len(self.corpus))
        return True

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Search BM25 index. Returns list of (metadata, score)."""
        if self.bm25 is None or not self.corpus:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        # Get top-k indices
        top_indices = scores.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            if idx < len(self.metadata):
                results.append((self.metadata[idx], score))
        return results

    @property
    def is_ready(self) -> bool:
        return self.bm25 is not None and len(self.corpus) > 0

    @property
    def count(self) -> int:
        return len(self.corpus) if self.corpus else 0
