"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ── Organization & Department ────────────────────────────────────

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    departments: List["DepartmentResponse"] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class DepartmentCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

# ── Auth ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


# ── User ─────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    organization_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Conversation ─────────────────────────────────────────────────

class ConversationListItem(BaseModel):
    id: str
    organization_id: Optional[str] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_company: Optional[str] = None
    subject: str
    category: Optional[str] = None
    priority: str
    status: str
    agent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_message: Optional[str] = None
    draft_confidence: Optional[float] = None
    draft_status: Optional[str] = None
    source_count: Optional[int] = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_company: Optional[str] = None
    subject: str
    category: Optional[str] = None
    priority: str
    status: str
    agent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    drafts: List["DraftResponse"] = []

    model_config = {"from_attributes": True}


# ── AI Draft ─────────────────────────────────────────────────────

class CitationItem(BaseModel):
    faq_id: str
    title: str
    snippet: str
    relevance_score: float
    version: Optional[str] = None
    updated_at: Optional[str] = None
    authority: Optional[str] = None
    category: Optional[str] = None


class ConfidenceDetail(BaseModel):
    score: float
    level: str
    reasons: List[str] = []
    retrieval_relevance: Optional[float] = None
    source_coverage: Optional[float] = None
    freshness: Optional[float] = None
    consistency: Optional[float] = None
    authority: Optional[float] = None
    answerability: Optional[float] = None


class KnowledgeGapInfo(BaseModel):
    needed: bool
    reason: Optional[str] = None
    missing_topic: Optional[str] = None


class EscalationInfo(BaseModel):
    required: bool
    reason: Optional[str] = None
    recommended_team: Optional[str] = None


class ToneCheck(BaseModel):
    professional: bool = True
    concise: bool = True
    empathetic: bool = True


class SourceConflictInfo(BaseModel):
    detected: bool = False
    reason: Optional[str] = None
    conflicting_sources: List[str] = []
    preferred_source: Optional[str] = None


class EvidenceCoverageInfo(BaseModel):
    score: float = 100.0
    covered: List[str] = []
    missing: List[str] = []


class DraftResponse(BaseModel):
    id: str
    conversation_id: str
    draft_reply: str
    short_summary: Optional[str] = None
    status: str
    confidence: ConfidenceDetail
    citations: List[CitationItem] = []
    knowledge_gap: KnowledgeGapInfo
    escalation: EscalationInfo
    source_conflict: SourceConflictInfo = SourceConflictInfo()
    evidence_coverage: EvidenceCoverageInfo = EvidenceCoverageInfo()
    tone_check: ToneCheck
    model_version: Optional[str] = None
    retrieval_latency_ms: Optional[float] = None
    generation_latency_ms: Optional[float] = None
    total_latency_ms: Optional[float] = None
    edited_reply: Optional[str] = None
    edit_distance: Optional[float] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateDraftRequest(BaseModel):
    tone: str = "professional"  # professional, empathetic, concise
    length: str = "standard"  # short, standard, detailed
    focus: str = "auto"  # auto, troubleshooting, explanation, next_steps


class ApproveDraftRequest(BaseModel):
    edited_reply: Optional[str] = None


class RegenerateDraftRequest(BaseModel):
    tone: str = "professional"
    length: str = "standard"
    focus: str = "auto"
    feedback: Optional[str] = None


# ── Knowledge ────────────────────────────────────────────────────

class KnowledgeDocResponse(BaseModel):
    id: str
    doc_id: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    department_id: Optional[str] = None
    title: str
    category: str
    document_type: Optional[str] = None
    authority: Optional[str] = None
    content: str
    keywords: List[str] = []
    version: str
    status: str
    owner: Optional[str] = None
    source_url: Optional[str] = None
    source_filename: Optional[str] = None
    usage_count: int = 0
    avg_relevance: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocCreate(BaseModel):
    doc_id: str
    organization_id: Optional[str] = None
    department_id: Optional[str] = None
    title: str
    category: str
    document_type: str = "faq"
    authority: str = "approved_faq"
    content: str
    keywords: List[str] = []
    version: str = "1.0"
    owner: Optional[str] = None
    source_url: Optional[str] = None


class KnowledgeDocUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    version: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None


# ── Knowledge Gap ────────────────────────────────────────────────

class KnowledgeGapResponse(BaseModel):
    id: str
    topic: str
    description: str
    question_pattern: Optional[str] = None
    frequency: int = 1
    impact: str = "medium"
    status: str = "open"
    recommended_action: Optional[str] = None
    conversation_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Escalation ───────────────────────────────────────────────────

class EscalationResponse(BaseModel):
    id: str
    conversation_id: str
    reason: str
    severity: str
    recommended_team: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Evaluation ───────────────────────────────────────────────────

class EvaluationResponse(BaseModel):
    id: str
    eval_type: str
    metric_name: str
    metric_value: float
    details: dict = {}
    dataset_version: Optional[str] = None
    model_version: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analytics ────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    total_conversations: int = 0
    total_drafts: int = 0
    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    avg_confidence: float = 0.0
    escalation_rate: float = 0.0
    knowledge_gap_count: int = 0
    avg_edit_distance: float = 0.0
    conversations_by_status: dict = {}
    conversations_by_priority: dict = {}
    conversations_by_category: dict = {}
    confidence_distribution: dict = {}
    drafts_over_time: List[dict] = []
    approval_over_time: List[dict] = []


# ── Model Insights ───────────────────────────────────────────────

class ModelInsightsResponse(BaseModel):
    current_model: str = ""
    base_model: str = ""
    fine_tuning_method: Optional[str] = None
    adapter_path: Optional[str] = None
    training_dataset_size: Optional[int] = None
    validation_loss: Optional[float] = None
    eval_metrics: dict = {}
    quantization: Optional[str] = None
    context_size: Optional[int] = None
    is_active: bool = False
    version: Optional[str] = None


# ── System ───────────────────────────────────────────────────────

class SystemHealthResponse(BaseModel):
    database: str = "unknown"
    rag_index: str = "unknown"
    embedding_model: str = "unknown"
    llm: str = "unknown"
    model_adapter: str = "unknown"


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    doc_id: str
    title: str
    snippet: str
    relevance_score: float
    category: str
    version: str


class FeedbackCreate(BaseModel):
    conversation_id: str
    draft_id: Optional[str] = None
    original_question: str
    ai_response: str
    human_action: str
    edited_response: Optional[str] = None
    rejection_reason: Optional[str] = None


# ── Audit ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    details: dict = {}
    ai_version: Optional[str] = None
    sources_used: List[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}
