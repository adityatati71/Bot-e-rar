"""SQLAlchemy ORM models for ResolveAI."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ────────────────────────────────────────────────────────

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, enum.Enum):
    NEW = "new"
    OPEN = "open"
    AI_DRAFTED = "ai_drafted"
    HUMAN_REVIEW = "human_review"
    EDITED = "edited"
    APPROVED = "approved"
    SENT = "sent"
    ESCALATED = "escalated"
    CLOSED = "closed"


class DraftStatus(str, enum.Enum):
    GENERATED = "generated"
    REVIEWED = "reviewed"
    EDITED = "edited"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATED = "regenerated"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class KBDocStatus(str, enum.Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class UserRole(str, enum.Enum):
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"


class MessageSender(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class DocumentAuthority(str, enum.Enum):
    OFFICIAL_POLICY = "official_policy"
    OFFICIAL_DOCS = "official_docs"
    APPROVED_FAQ = "approved_faq"
    INTERNAL_ARTICLE = "internal_article"
    AGENT_NOTES = "agent_notes"


class DocumentType(str, enum.Enum):
    FAQ = "faq"
    POLICY = "policy"
    DOCUMENTATION = "documentation"
    TROUBLESHOOTING = "troubleshooting"
    GUIDE = "guide"
    RELEASE_NOTES = "release_notes"
    INTERNAL = "internal"


# ── Models ───────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    departments = relationship("Department", back_populates="organization")
    documents = relationship("KnowledgeDocument", back_populates="organization")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, default=gen_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    organization = relationship("Organization", back_populates="departments")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.AGENT)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    conversations = relationship("Conversation", back_populates="agent")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=gen_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    category = Column(String, nullable=True)
    priority = Column(SAEnum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.NEW)
    agent_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    agent = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    drafts = relationship("AIDraft", back_populates="conversation", order_by="AIDraft.created_at.desc()")
    audit_logs = relationship("AuditLog", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender = Column(SAEnum(MessageSender), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    doc_id = Column(String, unique=True, nullable=False, index=True)  # e.g. KB-001
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    document_type = Column(SAEnum(DocumentType), default=DocumentType.FAQ)
    authority = Column(SAEnum(DocumentAuthority), default=DocumentAuthority.APPROVED_FAQ)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)
    version = Column(String, default="1.0")
    status = Column(SAEnum(KBDocStatus), default=KBDocStatus.ACTIVE)
    owner = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_filename = Column(String, nullable=True)
    effective_date = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    avg_relevance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("knowledge_documents.id"), nullable=False)
    organization_id = Column(String, nullable=True, index=True)  # denormalized for fast filtering
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    document = relationship("KnowledgeDocument", back_populates="chunks")


class AIDraft(Base):
    __tablename__ = "ai_drafts"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    draft_reply = Column(Text, nullable=False)
    short_summary = Column(Text, nullable=True)
    status = Column(SAEnum(DraftStatus), default=DraftStatus.GENERATED)
    confidence_score = Column(Float, default=0.0)
    confidence_level = Column(SAEnum(ConfidenceLevel), default=ConfidenceLevel.LOW)
    confidence_reasons = Column(JSON, default=list)
    confidence_details = Column(JSON, default=dict)  # retrieval_relevance, coverage, etc.
    citations = Column(JSON, default=list)
    knowledge_gap_needed = Column(Boolean, default=False)
    knowledge_gap_reason = Column(Text, nullable=True)
    knowledge_gap_topic = Column(String, nullable=True)
    escalation_required = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    tone_professional = Column(Boolean, default=True)
    tone_concise = Column(Boolean, default=True)
    tone_empathetic = Column(Boolean, default=True)
    model_version = Column(String, nullable=True)
    retrieval_latency_ms = Column(Float, nullable=True)
    generation_latency_ms = Column(Float, nullable=True)
    total_latency_ms = Column(Float, nullable=True)
    edited_reply = Column(Text, nullable=True)
    edit_distance = Column(Float, nullable=True)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    conversation = relationship("Conversation", back_populates="drafts")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String, primary_key=True, default=gen_uuid)
    draft_id = Column(String, ForeignKey("ai_drafts.id"), nullable=False)
    document_id = Column(String, ForeignKey("knowledge_documents.id"), nullable=False)
    doc_id_ref = Column(String, nullable=False)  # KB-001
    title = Column(String, nullable=False)
    snippet = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(String, primary_key=True, default=gen_uuid)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    question_pattern = Column(Text, nullable=True)
    frequency = Column(Integer, default=1)
    impact = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="open")  # open, in_progress, resolved
    recommended_action = Column(Text, nullable=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String, default="medium")
    recommended_team = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, reviewed, resolved
    created_at = Column(DateTime, default=utcnow)
    resolved_at = Column(DateTime, nullable=True)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, default=gen_uuid)
    eval_type = Column(String, nullable=False)  # rag, model, e2e
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    details = Column(JSON, default=dict)
    dataset_version = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    draft_id = Column(String, ForeignKey("ai_drafts.id"), nullable=True)
    original_question = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    human_action = Column(String, nullable=False)  # approved, edited, rejected
    edited_response = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    edit_distance = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    ai_version = Column(String, nullable=True)
    retrieval_version = Column(String, nullable=True)
    sources_used = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="audit_logs")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    base_model = Column(String, nullable=False)
    adapter_path = Column(String, nullable=True)
    fine_tuning_method = Column(String, nullable=True)
    training_dataset_size = Column(Integer, nullable=True)
    validation_loss = Column(Float, nullable=True)
    eval_metrics = Column(JSON, default=dict)
    quantization = Column(String, nullable=True)
    context_size = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class RetrievalRun(Base):
    __tablename__ = "retrieval_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    query = Column(Text, nullable=False)
    embedding_model = Column(String, nullable=True)
    index_version = Column(String, nullable=True)
    num_results = Column(Integer, default=0)
    latency_ms = Column(Float, nullable=True)
    scores = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)
