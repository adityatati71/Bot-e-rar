"""Full RAG pipeline: retrieve → context → confidence → citations.

V2: Tenant-aware retrieval, document authority, source conflicts,
    evidence coverage, answerability scoring.
"""
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone
import structlog

from rag.retriever import HybridRetriever

logger = structlog.get_logger()

# Authority weights: higher authority = higher trust
AUTHORITY_WEIGHTS = {
    "official_policy": 1.0,
    "official_docs": 0.85,
    "approved_faq": 0.7,
    "internal_article": 0.5,
    "agent_notes": 0.3,
}


class RAGPipeline:
    """End-to-end RAG pipeline for ResolveAI."""

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

    def process(
        self,
        query: str,
        top_k: int = 5,
        confidence_high: int = 80,
        confidence_medium: int = 60,
        organization_id: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> Dict:
        """
        Full RAG pipeline:
        1. Retrieve relevant evidence (tenant-filtered)
        2. Build context
        3. Generate citations
        4. Calculate grounding confidence (with authority)
        5. Detect knowledge gaps
        6. Detect source conflicts
        7. Calculate evidence coverage
        """
        start = time.time()

        # Step 1: Retrieve (tenant-aware with normalized matching)
        norm_org = organization_id.replace("_", "-").lower() if organization_id else None
        candidate_k = max(top_k * 4, 25)
        retrieval = self.retriever.retrieve(query, top_k=candidate_k)
        results = retrieval["results"]

        # Post-filter by organization if specified
        if norm_org:
            tenant_results = [
                (meta, score)
                for meta, score in results
                if (meta.get("organization_id", "").replace("_", "-").lower() == norm_org)
            ]
            if tenant_results:
                results = tenant_results
            else:
                # Fallback to unbranded/general docs
                results = [
                    (meta, score)
                    for meta, score in results
                    if not meta.get("organization_id")
                ]

        results = results[:top_k]

        # Further filter by department if specified
        if department_id:
            dept_results = [
                (meta, score)
                for meta, score in results
                if meta.get("department_id") == department_id
            ]
            # Only filter if there are dept-specific results, otherwise keep broader set
            if dept_results:
                results = dept_results

        # Step 2: Build evidence context
        evidence_context = self._build_context(results)

        # Step 3: Generate citations
        citations = self._build_citations(results)

        # Step 4: Calculate grounding confidence (with authority)
        confidence = self._calculate_confidence(
            results, confidence_high, confidence_medium
        )

        # Step 5: Detect knowledge gaps
        knowledge_gap = self._detect_knowledge_gap(results, query)

        # Step 6: Detect source conflicts
        source_conflict = self._detect_source_conflict(results)

        # Step 7: Calculate evidence coverage
        evidence_coverage = self._calculate_evidence_coverage(query, results)

        total_latency = (time.time() - start) * 1000

        return {
            "evidence_context": evidence_context,
            "citations": citations,
            "confidence": confidence,
            "knowledge_gap": knowledge_gap,
            "source_conflict": source_conflict,
            "evidence_coverage": evidence_coverage,
            "retrieval_stats": {
                "latency_ms": retrieval["latency_ms"],
                "dense_count": retrieval["dense_count"],
                "sparse_count": retrieval["sparse_count"],
                "reranked": retrieval["reranked"],
                "total_candidates": retrieval["total_candidates"],
                "final_results": len(results),
            },
            "total_latency_ms": round(total_latency, 2),
        }

    def _build_context(self, results: list) -> str:
        """Build context string from retrieved evidence for LLM."""
        if not results:
            return "No relevant knowledge base articles were found."

        context_parts = []
        for i, (meta, score) in enumerate(results, 1):
            doc_id = meta.get("doc_id", "unknown")
            title = meta.get("title", "Untitled")
            content = meta.get("content", meta.get("text", ""))
            version = meta.get("version", "")
            updated = meta.get("updated_at", "")
            authority = meta.get("authority", "")

            part = f"[Source {i}] {title} ({doc_id}, v{version})\n"
            if authority:
                part += f"Authority: {authority}\n"
            if updated:
                part += f"Last updated: {updated}\n"
            part += f"{content}\n"
            context_parts.append(part)

        return "\n---\n".join(context_parts)

    def _build_citations(self, results: list) -> List[Dict]:
        """Build citation objects from retrieved results."""
        citations = []
        for meta, score in results:
            citations.append({
                "faq_id": meta.get("doc_id", ""),
                "title": meta.get("title", ""),
                "snippet": (meta.get("content", meta.get("text", "")))[:300],
                "relevance_score": round(score, 4),
                "version": meta.get("version", ""),
                "updated_at": meta.get("updated_at", ""),
                "category": meta.get("category", ""),
                "authority": meta.get("authority", ""),
            })
        return citations

    def _calculate_confidence(
        self,
        results: list,
        high_threshold: int = 80,
        medium_threshold: int = 60,
    ) -> Dict:
        """
        Calculate grounding confidence from measurable signals.
        NOT by asking the LLM "how confident are you?"

        V2: Adds authority scoring.
        """
        if not results:
            return {
                "score": 0,
                "level": "low",
                "reasons": ["No relevant sources found"],
                "retrieval_relevance": 0,
                "source_coverage": 0,
                "freshness": 0,
                "consistency": 0,
                "authority": 0,
                "answerability": 0,
            }

        scores = [s for _, s in results]

        # 1. Retrieval relevance: average relevance of top results
        avg_relevance = sum(scores) / len(scores) if scores else 0
        retrieval_relevance = min(100, max(0, avg_relevance * 100))

        # 2. Source coverage: how many sources found (scaled)
        source_coverage = min(100, (len(results) / 3) * 100)

        # 3. Freshness: check how recently sources were updated
        freshness = self._calculate_freshness(results)

        # 4. Consistency: check if sources agree
        consistency = self._calculate_consistency(results)

        # 5. Authority: weighted by document authority level
        authority_score = self._calculate_authority(results)

        # 6. Answerability: how likely evidence actually answers the question
        answerability = self._calculate_answerability(results)

        # Weighted score (V2 weights)
        score = (
            retrieval_relevance * 0.25
            + source_coverage * 0.15
            + freshness * 0.15
            + consistency * 0.15
            + authority_score * 0.15
            + answerability * 0.15
        )
        score = round(min(100, max(0, score)), 1)

        # Level
        if score >= high_threshold:
            level = "high"
        elif score >= medium_threshold:
            level = "medium"
        else:
            level = "low"

        # Reasons
        reasons = []
        if retrieval_relevance > 70:
            reasons.append(f"{len(results)} highly relevant sources found")
        elif retrieval_relevance > 40:
            reasons.append(f"{len(results)} moderately relevant sources found")
        else:
            reasons.append("Low relevance in retrieved sources")

        if source_coverage >= 80:
            reasons.append("Strong evidence coverage")
        elif source_coverage >= 50:
            reasons.append("Moderate evidence coverage")
        else:
            reasons.append("Limited evidence coverage")

        if freshness >= 80:
            reasons.append("Sources are current")
        elif freshness >= 50:
            reasons.append("Some sources may need updating")
        else:
            reasons.append("Sources may be outdated")

        if consistency >= 80:
            reasons.append("No source conflicts detected")
        else:
            reasons.append("Potential source conflicts detected")

        if authority_score >= 80:
            reasons.append("High-authority sources used")
        elif authority_score >= 50:
            reasons.append("Moderate-authority sources")

        return {
            "score": score,
            "level": level,
            "reasons": reasons,
            "retrieval_relevance": round(retrieval_relevance, 1),
            "source_coverage": round(source_coverage, 1),
            "freshness": round(freshness, 1),
            "consistency": round(consistency, 1),
            "authority": round(authority_score, 1),
            "answerability": round(answerability, 1),
        }

    def _calculate_freshness(self, results: list) -> float:
        """Calculate freshness score based on document update dates."""
        now = datetime.now(timezone.utc)
        freshness_scores = []

        for meta, _ in results:
            updated = meta.get("updated_at", "")
            if not updated:
                freshness_scores.append(50)
                continue
            try:
                if isinstance(updated, str):
                    if "T" in updated:
                        update_date = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    else:
                        update_date = datetime.strptime(updated, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    update_date = updated

                days_old = (now - update_date).days
                if days_old <= 7:
                    freshness_scores.append(100)
                elif days_old <= 30:
                    freshness_scores.append(90)
                elif days_old <= 90:
                    freshness_scores.append(75)
                elif days_old <= 180:
                    freshness_scores.append(50)
                else:
                    freshness_scores.append(30)
            except (ValueError, TypeError):
                freshness_scores.append(50)

        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else 50

    def _calculate_consistency(self, results: list) -> float:
        """Basic consistency check — higher if sources are from related categories."""
        if len(results) <= 1:
            return 95

        categories = set()
        for meta, _ in results:
            cat = meta.get("category", "")
            if cat:
                categories.add(cat)

        if len(categories) <= 1:
            return 98
        elif len(categories) <= 2:
            return 90
        elif len(categories) <= 3:
            return 80
        else:
            return 70

    def _calculate_authority(self, results: list) -> float:
        """Calculate authority score from document authority levels."""
        if not results:
            return 0

        authority_scores = []
        for meta, _ in results:
            auth = meta.get("authority", "approved_faq")
            weight = AUTHORITY_WEIGHTS.get(auth, 0.5)
            authority_scores.append(weight * 100)

        return sum(authority_scores) / len(authority_scores) if authority_scores else 50

    def _calculate_answerability(self, results: list) -> float:
        """
        Estimate how likely the retrieved evidence actually answers the question.
        Based on top relevance score, number of sources, and score distribution.
        """
        if not results:
            return 0

        scores = [s for _, s in results]
        top_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # Strong top match indicates high answerability
        if top_score >= 0.8:
            base = 90
        elif top_score >= 0.5:
            base = 70
        elif top_score >= 0.3:
            base = 45
        else:
            base = 20

        # Multiple relevant sources increase answerability
        relevant_count = sum(1 for s in scores if s >= 0.3)
        bonus = min(10, relevant_count * 3)

        return min(100, base + bonus)

    def _detect_knowledge_gap(self, results: list, query: str) -> Dict:
        """Detect if the knowledge base cannot confidently answer."""
        if not results:
            return {
                "needed": True,
                "reason": "No relevant documentation was found for this query.",
                "missing_topic": query[:200],
            }

        scores = [s for _, s in results]
        max_score = max(scores) if scores else 0

        if max_score < 0.3:
            return {
                "needed": True,
                "reason": "Retrieved sources have very low relevance to the question.",
                "missing_topic": query[:200],
            }

        if len(results) == 1 and max_score < 0.5:
            return {
                "needed": True,
                "reason": "Only one weakly relevant source was found. The knowledge base may need additional documentation on this topic.",
                "missing_topic": query[:200],
            }

        return {
            "needed": False,
            "reason": None,
            "missing_topic": None,
        }

    def _detect_source_conflict(self, results: list) -> Dict:
        """
        Detect if retrieved sources contain conflicting information.
        Simple heuristic: check if sources from the same category
        have very different versions or contradictory authority levels.
        """
        if len(results) <= 1:
            return {"detected": False, "reason": None, "conflicting_sources": [], "preferred_source": None}

        # Group by category
        by_category: Dict[str, List] = {}
        for meta, score in results:
            cat = meta.get("category", "unknown")
            by_category.setdefault(cat, []).append((meta, score))

        for cat, items in by_category.items():
            if len(items) < 2:
                continue

            # Check version mismatch within same category
            versions = [(m.get("doc_id", ""), m.get("version", "1.0"), m.get("authority", ""), score) for m, score in items]
            if len(set(v[1] for v in versions)) > 1:
                # Different versions — prefer higher authority + newer version
                sorted_v = sorted(
                    versions,
                    key=lambda x: (AUTHORITY_WEIGHTS.get(x[2], 0.5), x[1]),
                    reverse=True,
                )
                if AUTHORITY_WEIGHTS.get(sorted_v[0][2], 0.5) != AUTHORITY_WEIGHTS.get(sorted_v[-1][2], 0.5):
                    return {
                        "detected": True,
                        "reason": f"Multiple sources in '{cat}' with different versions/authority levels.",
                        "conflicting_sources": [v[0] for v in versions],
                        "preferred_source": sorted_v[0][0],
                    }

        return {"detected": False, "reason": None, "conflicting_sources": [], "preferred_source": None}

    def _calculate_evidence_coverage(self, query: str, results: list) -> Dict:
        """
        Estimate how much of the query is covered by evidence.
        Simple approach: split query into requirement keywords,
        check how many are found in retrieved documents.
        """
        if not results:
            return {"score": 0.0, "covered": [], "missing": [query]}

        # Extract key topics from query
        stop_words = {"i", "my", "me", "the", "a", "an", "is", "are", "was", "were", "be",
                      "to", "of", "and", "in", "that", "it", "for", "do", "does", "can",
                      "how", "what", "when", "where", "why", "will", "would", "should",
                      "have", "has", "had", "not", "but", "or", "if", "from", "with",
                      "this", "at", "by", "we", "you", "your", "they", "them", "our"}

        query_terms = [w.strip("?.,!") for w in query.lower().split() if w.strip("?.,!") not in stop_words and len(w) > 2]
        if not query_terms:
            return {"score": 100.0, "covered": [], "missing": []}

        # Check which terms appear in evidence
        evidence_text = " ".join(
            meta.get("content", meta.get("text", "")).lower()
            for meta, _ in results
        )

        covered = [t for t in query_terms if t in evidence_text]
        missing = [t for t in query_terms if t not in evidence_text]

        coverage = (len(covered) / len(query_terms)) * 100 if query_terms else 100
        return {
            "score": round(coverage, 1),
            "covered": covered[:10],
            "missing": missing[:5],
        }
