"""Draft generation, approval, and management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from app.db.database import get_db
from app.models.models import (
    Conversation, Message, AIDraft, AuditLog, Feedback,
    KnowledgeGap, Escalation, User,
    TicketStatus, DraftStatus, ConfidenceLevel, MessageSender,
)
from app.schemas.schemas import (
    GenerateDraftRequest, ApproveDraftRequest, RegenerateDraftRequest,
    DraftResponse,
)
from app.security.auth import get_current_user
from app.api.routes.conversations import _draft_to_response

router = APIRouter()


def _get_copilot():
    """Get the copilot service from app state."""
    from app.main import copilot_service
    if not copilot_service:
        raise HTTPException(status_code=503, detail="AI copilot service is not available. Check system status.")
    return copilot_service


@router.post("/conversations/{conversation_id}/draft", response_model=DraftResponse)
async def generate_draft(
    conversation_id: str,
    request: Optional[GenerateDraftRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an AI draft for a conversation."""
    req = request or GenerateDraftRequest()
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get the latest customer message
    customer_msg = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender == MessageSender.CUSTOMER,
    ).order_by(Message.created_at.desc()).first()

    if not customer_msg:
        raise HTTPException(status_code=400, detail="No customer message found")

    # Run copilot (tenant-aware)
    copilot = _get_copilot()
    result = await copilot.process_query(
        query=customer_msg.content,
        tone=req.tone,
        length=req.length,
        focus=req.focus,
        organization_id=conv.organization_id,
        department_id=conv.department_id,
    )

    # Determine confidence level
    conf_score = result["confidence"]["score"]
    if conf_score >= 80:
        conf_level = ConfidenceLevel.HIGH
    elif conf_score >= 60:
        conf_level = ConfidenceLevel.MEDIUM
    else:
        conf_level = ConfidenceLevel.LOW

    # Create draft
    draft = AIDraft(
        conversation_id=conversation_id,
        draft_reply=result["draft_reply"],
        short_summary=result.get("short_summary", ""),
        status=DraftStatus.GENERATED,
        confidence_score=conf_score,
        confidence_level=conf_level,
        confidence_reasons=result["confidence"]["reasons"],
        confidence_details={
            "retrieval_relevance": result["confidence"].get("retrieval_relevance", 0),
            "source_coverage": result["confidence"].get("source_coverage", 0),
            "freshness": result["confidence"].get("freshness", 0),
            "consistency": result["confidence"].get("consistency", 0),
            "authority": result["confidence"].get("authority", 0),
            "answerability": result["confidence"].get("answerability", 0),
        },
        citations=result["citations"],
        knowledge_gap_needed=result["knowledge_gap"]["needed"],
        knowledge_gap_reason=result["knowledge_gap"].get("reason"),
        knowledge_gap_topic=result["knowledge_gap"].get("missing_topic"),
        escalation_required=result["escalation"]["required"],
        escalation_reason=result["escalation"].get("reason"),
        tone_professional=result.get("tone_check", {}).get("professional", True),
        tone_concise=result.get("tone_check", {}).get("concise", True),
        tone_empathetic=result.get("tone_check", {}).get("empathetic", True),
        model_version=result.get("model_version", ""),
        retrieval_latency_ms=result.get("retrieval_latency_ms", 0),
        generation_latency_ms=result.get("generation_latency_ms", 0),
        total_latency_ms=result.get("total_latency_ms", 0),
    )
    db.add(draft)

    # Update conversation status
    conv.status = TicketStatus.AI_DRAFTED
    conv.updated_at = datetime.now(timezone.utc)

    # Create knowledge gap record if detected
    if result["knowledge_gap"]["needed"]:
        gap = KnowledgeGap(
            topic=result["knowledge_gap"].get("missing_topic", "Unknown"),
            description=result["knowledge_gap"].get("reason", ""),
            question_pattern=customer_msg.content[:500],
            frequency=1,
            impact="medium" if conf_score > 40 else "high",
            status="open",
            recommended_action="Review and create documentation for this topic.",
            conversation_id=conversation_id,
        )
        db.add(gap)

    # Create escalation record if detected
    if result["escalation"]["required"]:
        esc = Escalation(
            conversation_id=conversation_id,
            reason=result["escalation"].get("reason", ""),
            severity="high",
            recommended_team=result["escalation"].get("recommended_team"),
            status="pending",
        )
        db.add(esc)
        conv.status = TicketStatus.ESCALATED

    # Audit log
    audit = AuditLog(
        conversation_id=conversation_id,
        user_id=current_user.id,
        action="draft_generated",
        previous_state="new",
        new_state="ai_drafted",
        details={
            "confidence": conf_score,
            "citations_count": len(result["citations"]),
            "knowledge_gap": result["knowledge_gap"]["needed"],
            "escalation": result["escalation"]["required"],
            "latency_ms": result.get("total_latency_ms", 0),
        },
        ai_version=result.get("model_version", ""),
        sources_used=[c.get("faq_id", "") for c in result["citations"]],
    )
    db.add(audit)

    db.commit()
    db.refresh(draft)

    return _draft_to_response(draft)


@router.post("/{draft_id}/approve")
async def approve_draft(
    draft_id: str,
    request: ApproveDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a draft (with optional edits)."""
    draft = db.query(AIDraft).filter(AIDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    now = datetime.now(timezone.utc)

    # Calculate edit distance if edited
    edit_distance = 0.0
    if request.edited_reply and request.edited_reply != draft.draft_reply:
        draft.edited_reply = request.edited_reply
        # Simple edit distance: character-level difference ratio
        original = draft.draft_reply
        edited = request.edited_reply
        max_len = max(len(original), len(edited))
        if max_len > 0:
            # Count character differences
            diff_count = sum(1 for a, b in zip(original, edited) if a != b)
            diff_count += abs(len(original) - len(edited))
            edit_distance = round(diff_count / max_len, 4)
        draft.edit_distance = edit_distance
        draft.status = DraftStatus.EDITED

    draft.status = DraftStatus.APPROVED
    draft.approved_by = current_user.id
    draft.approved_at = now

    # Update conversation
    conv = db.query(Conversation).filter(Conversation.id == draft.conversation_id).first()
    if conv:
        prev_status = conv.status.value if hasattr(conv.status, 'value') else str(conv.status)
        conv.status = TicketStatus.APPROVED
        conv.updated_at = now

    # Add agent message
    final_reply = request.edited_reply if request.edited_reply else draft.draft_reply
    agent_msg = Message(
        conversation_id=draft.conversation_id,
        sender=MessageSender.AGENT,
        content=final_reply,
        created_at=now,
    )
    db.add(agent_msg)

    # Feedback record
    customer_msg = db.query(Message).filter(
        Message.conversation_id == draft.conversation_id,
        Message.sender == MessageSender.CUSTOMER,
    ).order_by(Message.created_at.desc()).first()

    fb = Feedback(
        conversation_id=draft.conversation_id,
        draft_id=draft_id,
        original_question=customer_msg.content if customer_msg else "",
        ai_response=draft.draft_reply,
        human_action="edited" if edit_distance > 0 else "approved",
        edited_response=request.edited_reply,
        edit_distance=edit_distance,
    )
    db.add(fb)

    # Audit log
    audit = AuditLog(
        conversation_id=draft.conversation_id,
        user_id=current_user.id,
        action="draft_approved",
        previous_state="ai_drafted",
        new_state="approved",
        details={
            "edit_distance": edit_distance,
            "was_edited": edit_distance > 0,
        },
        ai_version=draft.model_version,
        sources_used=[c.get("faq_id", "") for c in (draft.citations or [])],
    )
    db.add(audit)

    db.commit()

    return {
        "status": "approved",
        "draft_id": draft_id,
        "edit_distance": edit_distance,
        "approved_at": now.isoformat(),
    }


@router.post("/{draft_id}/reject")
async def reject_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a draft."""
    draft = db.query(AIDraft).filter(AIDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.status = DraftStatus.REJECTED
    draft.updated_at = datetime.now(timezone.utc)

    # Feedback
    customer_msg = db.query(Message).filter(
        Message.conversation_id == draft.conversation_id,
        Message.sender == MessageSender.CUSTOMER,
    ).order_by(Message.created_at.desc()).first()

    fb = Feedback(
        conversation_id=draft.conversation_id,
        draft_id=draft_id,
        original_question=customer_msg.content if customer_msg else "",
        ai_response=draft.draft_reply,
        human_action="rejected",
    )
    db.add(fb)

    # Audit log
    audit = AuditLog(
        conversation_id=draft.conversation_id,
        user_id=current_user.id,
        action="draft_rejected",
        previous_state="ai_drafted",
        new_state="rejected",
        ai_version=draft.model_version,
    )
    db.add(audit)

    db.commit()
    return {"status": "rejected", "draft_id": draft_id}


@router.post("/{draft_id}/regenerate", response_model=DraftResponse)
async def regenerate_draft(
    draft_id: str,
    request: RegenerateDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerate a draft with different parameters."""
    old_draft = db.query(AIDraft).filter(AIDraft.id == draft_id).first()
    if not old_draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    old_draft.status = DraftStatus.REGENERATED

    # Generate new draft by calling the conversation draft endpoint logic
    conv = db.query(Conversation).filter(Conversation.id == old_draft.conversation_id).first()
    customer_msg = db.query(Message).filter(
        Message.conversation_id == old_draft.conversation_id,
        Message.sender == MessageSender.CUSTOMER,
    ).order_by(Message.created_at.desc()).first()

    if not customer_msg:
        raise HTTPException(status_code=400, detail="No customer message found")

    copilot = _get_copilot()
    result = await copilot.process_query(
        query=customer_msg.content,
        tone=request.tone,
        length=request.length,
        focus=request.focus,
    )

    conf_score = result["confidence"]["score"]
    conf_level = ConfidenceLevel.HIGH if conf_score >= 80 else (ConfidenceLevel.MEDIUM if conf_score >= 60 else ConfidenceLevel.LOW)

    new_draft = AIDraft(
        conversation_id=old_draft.conversation_id,
        draft_reply=result["draft_reply"],
        short_summary=result.get("short_summary", ""),
        status=DraftStatus.GENERATED,
        confidence_score=conf_score,
        confidence_level=conf_level,
        confidence_reasons=result["confidence"]["reasons"],
        confidence_details={
            "retrieval_relevance": result["confidence"].get("retrieval_relevance", 0),
            "source_coverage": result["confidence"].get("source_coverage", 0),
            "freshness": result["confidence"].get("freshness", 0),
            "consistency": result["confidence"].get("consistency", 0),
        },
        citations=result["citations"],
        knowledge_gap_needed=result["knowledge_gap"]["needed"],
        knowledge_gap_reason=result["knowledge_gap"].get("reason"),
        knowledge_gap_topic=result["knowledge_gap"].get("missing_topic"),
        escalation_required=result["escalation"]["required"],
        escalation_reason=result["escalation"].get("reason"),
        model_version=result.get("model_version", ""),
        retrieval_latency_ms=result.get("retrieval_latency_ms", 0),
        generation_latency_ms=result.get("generation_latency_ms", 0),
        total_latency_ms=result.get("total_latency_ms", 0),
    )
    db.add(new_draft)

    audit = AuditLog(
        conversation_id=old_draft.conversation_id,
        user_id=current_user.id,
        action="draft_regenerated",
        previous_state="ai_drafted",
        new_state="ai_drafted",
        details={"previous_draft_id": draft_id, "new_tone": request.tone},
        ai_version=result.get("model_version", ""),
    )
    db.add(audit)

    db.commit()
    db.refresh(new_draft)

    return _draft_to_response(new_draft)


@router.post("/{draft_id}/escalate")
async def escalate_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Escalate a conversation from draft."""
    draft = db.query(AIDraft).filter(AIDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    conv = db.query(Conversation).filter(Conversation.id == draft.conversation_id).first()
    if conv:
        conv.status = TicketStatus.ESCALATED
        conv.updated_at = datetime.now(timezone.utc)

    esc = Escalation(
        conversation_id=draft.conversation_id,
        reason=draft.escalation_reason or "Manually escalated by agent",
        severity="high",
        recommended_team="Senior Support",
        status="pending",
    )
    db.add(esc)

    audit = AuditLog(
        conversation_id=draft.conversation_id,
        user_id=current_user.id,
        action="escalated",
        previous_state="ai_drafted",
        new_state="escalated",
        ai_version=draft.model_version,
    )
    db.add(audit)

    db.commit()
    return {"status": "escalated", "draft_id": draft_id}
