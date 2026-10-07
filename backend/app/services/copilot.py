"""Support Copilot orchestrator — the main AI workflow engine."""
import time
import re
from typing import Dict, Optional
from datetime import datetime, timezone
import structlog

from app.llm.service import LLMService
from rag.pipeline import RAGPipeline
from app.security.auth import detect_prompt_injection

logger = structlog.get_logger()

# Escalation keyword patterns
ESCALATION_PATTERNS = [
    (r"\b(hack|hacked|hacking|compromised|breach|breached)\b", "Potential security incident", "Security Support"),
    (r"\b(stolen|unauthorized access|someone accessed|account takeover)\b", "Suspected unauthorized access", "Security Support"),
    (r"\b(fraud|fraudulent|scam)\b", "Potential fraud detected", "Security Support"),
    (r"\b(lawyer|attorney|legal action|lawsuit|sue)\b", "Legal concern raised", "Legal Team"),
    (r"\b(gdpr|data protection|privacy request|delete my data|right to erasure)\b", "Privacy/compliance request", "Legal Team"),
    (r"\b(ssn|social security|credit card number|bank account)\b", "Sensitive PII detected", "Security Support"),
]


class SupportCopilotService:
    """
    The main orchestrator that combines:
    - Intent classification
    - Sensitive content detection
    - RAG retrieval
    - LLM generation
    - Citation validation
    - Confidence calculation
    - Knowledge gap detection
    - Escalation detection
    """

    def __init__(self, rag_pipeline: RAGPipeline, llm_service: LLMService):
        self.rag = rag_pipeline
        self.llm = llm_service

    async def process_query(
        self,
        query: str,
        tone: str = "professional",
        length: str = "standard",
        focus: str = "auto",
        confidence_high: int = 80,
        confidence_medium: int = 60,
        organization_id: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> Dict:
        """
        Full support copilot workflow:
        1. Check for prompt injection
        2. Detect escalation triggers
        3. Retrieve knowledge
        4. Generate response with evidence
        5. Combine all signals into structured output
        """
        start = time.time()

        # Step 1: Prompt injection check
        is_injection = detect_prompt_injection(query)
        if is_injection:
            logger.warning("prompt_injection_detected", query=query[:100])

        # Step 2: Escalation detection
        escalation = self._detect_escalation(query)

        # Step 3: RAG retrieval (tenant-aware)
        rag_result = self.rag.process(
            query,
            top_k=5,
            confidence_high=confidence_high,
            confidence_medium=confidence_medium,
            organization_id=organization_id,
            department_id=department_id,
        )

        # Step 4: Generate response
        if is_injection:
            llm_result = {
                "draft_reply": "I appreciate your message. I'm here to help with CloudDesk-related questions. Could you please describe the specific issue you're experiencing?",
                "short_summary": "Redirected potentially manipulative input to legitimate support.",
                "tone_check": {"professional": True, "concise": True, "empathetic": True},
                "generation_latency_ms": 0,
            }
        else:
            llm_result = await self.llm.generate_support_response(
                customer_query=query,
                evidence_context=rag_result["evidence_context"],
                tone=tone,
                length=length,
                focus=focus,
            )

        total_latency = (time.time() - start) * 1000

        # Combine everything
        return {
            "draft_reply": llm_result.get("draft_reply", ""),
            "short_summary": llm_result.get("short_summary", ""),
            "confidence": rag_result["confidence"],
            "citations": rag_result["citations"],
            "knowledge_gap": rag_result["knowledge_gap"],
            "source_conflict": rag_result.get("source_conflict", {"detected": False}),
            "evidence_coverage": rag_result.get("evidence_coverage", {"score": 100.0, "covered": [], "missing": []}),
            "escalation": escalation,
            "tone_check": llm_result.get("tone_check", {
                "professional": True,
                "concise": True,
                "empathetic": True,
            }),
            "retrieval_stats": rag_result["retrieval_stats"],
            "retrieval_latency_ms": rag_result["retrieval_stats"]["latency_ms"],
            "generation_latency_ms": llm_result.get("generation_latency_ms", 0),
            "total_latency_ms": round(total_latency, 2),
            "model_version": "resolveai-support-v0.1",
            "prompt_injection_detected": is_injection,
        }

    def _detect_escalation(self, query: str) -> Dict:
        """Detect if a query requires escalation based on patterns."""
        query_lower = query.lower()

        for pattern, reason, team in ESCALATION_PATTERNS:
            if re.search(pattern, query_lower):
                return {
                    "required": True,
                    "reason": reason,
                    "recommended_team": team,
                }

        return {
            "required": False,
            "reason": None,
            "recommended_team": None,
        }
