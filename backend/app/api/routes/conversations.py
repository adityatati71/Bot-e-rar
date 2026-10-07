"""Conversation and message routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from app.db.database import get_db
from app.models.models import Conversation, Message, AIDraft, User, TicketPriority, TicketStatus, MessageSender
from app.schemas.schemas import ConversationListItem, ConversationDetail, MessageResponse, DraftResponse
from app.security.auth import get_current_user

router = APIRouter()


class CreateConversationRequest(BaseModel):
    customer_name: str
    customer_email: str = ""
    customer_company: str = ""
    subject: str
    category: str = "General"
    priority: str = "medium"
    message: str
    organization_id: str = ""


@router.post("", response_model=ConversationDetail)
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation with an initial customer message."""
    import uuid
    conv_id = f"conv-{uuid.uuid4().hex[:8]}"
    msg_id = f"msg-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # Map priority string to enum
    priority_map = {
        "urgent": TicketPriority.URGENT,
        "high": TicketPriority.HIGH,
        "medium": TicketPriority.MEDIUM,
        "low": TicketPriority.LOW,
    }
    priority = priority_map.get(request.priority.lower(), TicketPriority.MEDIUM)

    conv = Conversation(
        id=conv_id,
        organization_id=request.organization_id or None,
        customer_name=request.customer_name,
        customer_email=request.customer_email,
        customer_company=request.customer_company,
        subject=request.subject,
        category=request.category,
        priority=priority,
        status=TicketStatus.NEW,
        agent_id=current_user.id,
        created_at=now,
    )
    db.add(conv)

    msg = Message(
        id=msg_id,
        conversation_id=conv_id,
        sender=MessageSender.CUSTOMER,
        content=request.message,
        created_at=now,
    )
    db.add(msg)
    db.commit()

    return ConversationDetail(
        id=conv.id,
        customer_name=conv.customer_name,
        customer_email=conv.customer_email,
        customer_company=conv.customer_company,
        subject=request.subject,
        category=request.category,
        priority=request.priority,
        status="new",
        agent_id=current_user.id,
        created_at=now,
        updated_at=now,
        messages=[MessageResponse.model_validate(msg)],
        drafts=[],
    )


def _draft_to_response(draft: AIDraft) -> DraftResponse:
    """Convert AIDraft model to DraftResponse schema."""
    citations = draft.citations or []
    confidence_details = draft.confidence_details or {}

    return DraftResponse(
        id=draft.id,
        conversation_id=draft.conversation_id,
        draft_reply=draft.draft_reply,
        short_summary=draft.short_summary,
        status=draft.status.value if hasattr(draft.status, 'value') else str(draft.status),
        confidence={
            "score": draft.confidence_score or 0,
            "level": draft.confidence_level.value if hasattr(draft.confidence_level, 'value') else str(draft.confidence_level or "low"),
            "reasons": draft.confidence_reasons or [],
            "retrieval_relevance": confidence_details.get("retrieval_relevance"),
            "source_coverage": confidence_details.get("source_coverage"),
            "freshness": confidence_details.get("freshness"),
            "consistency": confidence_details.get("consistency"),
            "authority": confidence_details.get("authority"),
            "answerability": confidence_details.get("answerability"),
        },
        citations=citations,
        knowledge_gap={
            "needed": draft.knowledge_gap_needed or False,
            "reason": draft.knowledge_gap_reason,
            "missing_topic": draft.knowledge_gap_topic,
        },
        escalation={
            "required": draft.escalation_required or False,
            "reason": draft.escalation_reason,
        },
        tone_check={
            "professional": draft.tone_professional if draft.tone_professional is not None else True,
            "concise": draft.tone_concise if draft.tone_concise is not None else True,
            "empathetic": draft.tone_empathetic if draft.tone_empathetic is not None else True,
        },
        model_version=draft.model_version,
        retrieval_latency_ms=draft.retrieval_latency_ms,
        generation_latency_ms=draft.generation_latency_ms,
        total_latency_ms=draft.total_latency_ms,
        edited_reply=draft.edited_reply,
        edit_distance=draft.edit_distance,
        approved_at=draft.approved_at,
        created_at=draft.created_at,
    )


@router.get("", response_model=List[ConversationListItem])
async def list_conversations(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Conversation).order_by(Conversation.updated_at.desc())

    if organization_id:
        query = query.filter(Conversation.organization_id == organization_id)
    if status:
        query = query.filter(Conversation.status == status)
    if priority:
        query = query.filter(Conversation.priority == priority)
    if category:
        query = query.filter(Conversation.category == category)

    conversations = query.all()
    result = []
    for conv in conversations:
        # Get latest message
        latest_msg = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.desc()).first()

        # Get latest draft
        latest_draft = db.query(AIDraft).filter(
            AIDraft.conversation_id == conv.id
        ).order_by(AIDraft.created_at.desc()).first()

        item = ConversationListItem(
            id=conv.id,
            organization_id=conv.organization_id,
            customer_name=conv.customer_name,
            customer_email=conv.customer_email,
            customer_company=conv.customer_company,
            subject=conv.subject,
            category=conv.category,
            priority=conv.priority.value if hasattr(conv.priority, 'value') else str(conv.priority),
            status=conv.status.value if hasattr(conv.status, 'value') else str(conv.status),
            agent_id=conv.agent_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            latest_message=latest_msg.content[:200] if latest_msg else None,
            draft_confidence=latest_draft.confidence_score if latest_draft else None,
            draft_status=latest_draft.status.value if latest_draft and hasattr(latest_draft.status, 'value') else (str(latest_draft.status) if latest_draft else None),
            source_count=len(latest_draft.citations) if latest_draft and latest_draft.citations else None,
        )
        result.append(item)

    return result


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    drafts = db.query(AIDraft).filter(
        AIDraft.conversation_id == conversation_id
    ).order_by(AIDraft.created_at.desc()).all()

    # Get org name
    from app.models.models import Organization
    org_name = None
    if conv.organization_id:
        org = db.query(Organization).filter(Organization.id == conv.organization_id).first()
        if org:
            org_name = org.name

    return ConversationDetail(
        id=conv.id,
        organization_id=conv.organization_id,
        organization_name=org_name,
        customer_name=conv.customer_name,
        customer_email=conv.customer_email,
        customer_company=conv.customer_company,
        subject=conv.subject,
        category=conv.category,
        priority=conv.priority.value if hasattr(conv.priority, 'value') else str(conv.priority),
        status=conv.status.value if hasattr(conv.status, 'value') else str(conv.status),
        agent_id=conv.agent_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
        drafts=[_draft_to_response(d) for d in drafts],
    )
