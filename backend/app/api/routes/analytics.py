"""Analytics, evaluation, model insights, audit, and feedback routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models.models import (
    Conversation, AIDraft, KnowledgeGap, Feedback, Evaluation,
    ModelVersion, AuditLog, User,
    TicketStatus, DraftStatus,
)
from app.schemas.schemas import (
    AnalyticsResponse, EvaluationResponse, ModelInsightsResponse,
    AuditLogResponse, FeedbackCreate,
)
from app.security.auth import get_current_user

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_conversations = db.query(Conversation).count()
    total_drafts = db.query(AIDraft).count()

    approved = db.query(AIDraft).filter(AIDraft.status == DraftStatus.APPROVED).count()
    rejected = db.query(AIDraft).filter(AIDraft.status == DraftStatus.REJECTED).count()

    approval_rate = (approved / total_drafts * 100) if total_drafts > 0 else 0
    rejection_rate = (rejected / total_drafts * 100) if total_drafts > 0 else 0

    avg_conf = db.query(func.avg(AIDraft.confidence_score)).scalar() or 0

    escalated = db.query(Conversation).filter(Conversation.status == TicketStatus.ESCALATED).count()
    escalation_rate = (escalated / total_conversations * 100) if total_conversations > 0 else 0

    gap_count = db.query(KnowledgeGap).filter(KnowledgeGap.status == "open").count()

    avg_edit = db.query(func.avg(Feedback.edit_distance)).filter(
        Feedback.edit_distance.isnot(None)
    ).scalar() or 0

    # Status distribution
    status_counts = {}
    for status_val in TicketStatus:
        count = db.query(Conversation).filter(Conversation.status == status_val).count()
        if count > 0:
            status_counts[status_val.value] = count

    # Priority distribution
    priority_counts = {}
    for row in db.query(Conversation.priority, func.count()).group_by(Conversation.priority).all():
        p = row[0].value if hasattr(row[0], 'value') else str(row[0])
        priority_counts[p] = row[1]

    # Category distribution
    category_counts = {}
    for row in db.query(Conversation.category, func.count()).group_by(Conversation.category).all():
        if row[0]:
            category_counts[row[0]] = row[1]

    # Confidence distribution
    high = db.query(AIDraft).filter(AIDraft.confidence_score >= 80).count()
    medium = db.query(AIDraft).filter(AIDraft.confidence_score >= 60, AIDraft.confidence_score < 80).count()
    low = db.query(AIDraft).filter(AIDraft.confidence_score < 60).count()

    return AnalyticsResponse(
        total_conversations=total_conversations,
        total_drafts=total_drafts,
        approval_rate=round(approval_rate, 1),
        rejection_rate=round(rejection_rate, 1),
        avg_confidence=round(float(avg_conf), 1),
        escalation_rate=round(escalation_rate, 1),
        knowledge_gap_count=gap_count,
        avg_edit_distance=round(float(avg_edit), 4),
        conversations_by_status=status_counts,
        conversations_by_priority=priority_counts,
        conversations_by_category=category_counts,
        confidence_distribution={"high": high, "medium": medium, "low": low},
    )


@router.get("/evaluation", response_model=List[EvaluationResponse])
async def get_evaluations(
    eval_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Evaluation).order_by(Evaluation.created_at.desc())
    if eval_type:
        query = query.filter(Evaluation.eval_type == eval_type)
    return [EvaluationResponse.model_validate(e) for e in query.all()]


@router.get("/model", response_model=ModelInsightsResponse)
async def get_model_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    if not model:
        return ModelInsightsResponse()

    return ModelInsightsResponse(
        current_model=model.name,
        base_model=model.base_model,
        fine_tuning_method=model.fine_tuning_method,
        adapter_path=model.adapter_path,
        training_dataset_size=model.training_dataset_size,
        validation_loss=model.validation_loss,
        eval_metrics=model.eval_metrics or {},
        quantization=model.quantization,
        context_size=model.context_size,
        is_active=model.is_active,
        version=model.name.split("-")[-1] if "-" in model.name else "v0.1",
    )


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    conversation_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if conversation_id:
        query = query.filter(AuditLog.conversation_id == conversation_id)
    return [AuditLogResponse.model_validate(a) for a in query.limit(limit).all()]


@router.post("/feedback")
async def create_feedback(
    request: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fb = Feedback(
        conversation_id=request.conversation_id,
        draft_id=request.draft_id,
        original_question=request.original_question,
        ai_response=request.ai_response,
        human_action=request.human_action,
        edited_response=request.edited_response,
        rejection_reason=request.rejection_reason,
    )
    db.add(fb)
    db.commit()
    return {"status": "feedback_recorded"}
