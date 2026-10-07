"""Knowledge base routes — V2 with multi-tenant, upload, and re-index."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import os
import uuid
import re
from app.db.database import get_db
from app.models.models import (
    KnowledgeDocument, KnowledgeChunk, KnowledgeGap, User, Organization,
    KBDocStatus, DocumentAuthority, DocumentType,
)
from app.schemas.schemas import (
    KnowledgeDocResponse, KnowledgeDocCreate, KnowledgeDocUpdate,
    KnowledgeGapResponse, SearchRequest, SearchResult,
)
from app.security.auth import get_current_user

router = APIRouter()


def _doc_to_response(doc: KnowledgeDocument) -> KnowledgeDocResponse:
    """Convert DB document to response schema with org name."""
    org_name = None
    if doc.organization and doc.organization.name:
        org_name = doc.organization.name
    return KnowledgeDocResponse(
        id=doc.id,
        doc_id=doc.doc_id,
        organization_id=doc.organization_id,
        organization_name=org_name,
        department_id=doc.department_id,
        title=doc.title,
        category=doc.category,
        document_type=doc.document_type.value if doc.document_type else None,
        authority=doc.authority.value if doc.authority else None,
        content=doc.content,
        keywords=doc.keywords or [],
        version=doc.version,
        status=doc.status.value if doc.status else "active",
        owner=doc.owner,
        source_url=doc.source_url,
        source_filename=doc.source_filename,
        usage_count=doc.usage_count or 0,
        avg_relevance=doc.avg_relevance or 0.0,
        created_at=doc.created_at,
        updated_at=doc.updated_at or doc.created_at,
    )


@router.get("", response_model=List[KnowledgeDocResponse])
async def list_knowledge(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc())

    if organization_id:
        query = query.filter(KnowledgeDocument.organization_id == organization_id)
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    if status:
        query = query.filter(KnowledgeDocument.status == status)
    if search:
        query = query.filter(
            KnowledgeDocument.title.ilike(f"%{search}%") |
            KnowledgeDocument.content.ilike(f"%{search}%")
        )

    return [_doc_to_response(doc) for doc in query.all()]


@router.get("/categories")
async def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = db.query(KnowledgeDocument.category).distinct().all()
    return [d[0] for d in docs if d[0]]


@router.get("/gaps", response_model=List[KnowledgeGapResponse])
async def list_gaps(
    status: Optional[str] = None,
    impact: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(KnowledgeGap).order_by(KnowledgeGap.created_at.desc())
    if status:
        query = query.filter(KnowledgeGap.status == status)
    if impact:
        query = query.filter(KnowledgeGap.impact == impact)
    return [KnowledgeGapResponse.model_validate(g) for g in query.all()]


@router.get("/health")
async def knowledge_health(
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Knowledge base health overview."""
    query = db.query(KnowledgeDocument)
    if organization_id:
        query = query.filter(KnowledgeDocument.organization_id == organization_id)

    all_docs = query.all()
    active_docs = [d for d in all_docs if d.status == KBDocStatus.ACTIVE]

    now = datetime.now(timezone.utc)

    def _days_since(dt):
        if dt is None:
            return 999
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).days

    fresh = sum(1 for d in active_docs if _days_since(d.updated_at) <= 30)
    stale = sum(1 for d in active_docs if _days_since(d.updated_at) > 90)

    categories = set(d.category for d in active_docs if d.category)
    gaps = db.query(KnowledgeGap).filter(KnowledgeGap.status == "open").count()

    freshness = (fresh / len(active_docs) * 100) if active_docs else 0
    coverage = max(0, 100 - gaps * 8)

    return {
        "total_documents": len(all_docs),
        "active_documents": len(active_docs),
        "categories": len(categories),
        "fresh_documents": fresh,
        "stale_documents": stale,
        "open_gaps": gaps,
        "freshness_score": round(freshness, 1),
        "coverage_score": round(coverage, 1),
        "health_score": round((freshness * 0.4 + coverage * 0.6), 1),
    }


@router.get("/{doc_id}", response_model=KnowledgeDocResponse)
async def get_knowledge_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(KnowledgeDocument).filter(
        (KnowledgeDocument.id == doc_id) | (KnowledgeDocument.doc_id == doc_id)
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_to_response(doc)


@router.post("", response_model=KnowledgeDocResponse)
async def create_knowledge_doc(
    request: KnowledgeDocCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Map string to enum
    authority_map = {a.value: a for a in DocumentAuthority}
    doc_type_map = {t.value: t for t in DocumentType}

    doc = KnowledgeDocument(
        doc_id=request.doc_id,
        organization_id=request.organization_id,
        department_id=request.department_id,
        title=request.title,
        category=request.category,
        document_type=doc_type_map.get(request.document_type, DocumentType.FAQ),
        authority=authority_map.get(request.authority, DocumentAuthority.APPROVED_FAQ),
        content=request.content,
        keywords=request.keywords,
        version=request.version,
        owner=request.owner,
        source_url=request.source_url,
        effective_date=datetime.now(timezone.utc),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _doc_to_response(doc)


@router.put("/{doc_id}", response_model=KnowledgeDocResponse)
async def update_knowledge_doc(
    doc_id: str,
    request: KnowledgeDocUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(KnowledgeDocument).filter(
        (KnowledgeDocument.id == doc_id) | (KnowledgeDocument.doc_id == doc_id)
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    db.commit()
    db.refresh(doc)
    return _doc_to_response(doc)


@router.post("/{doc_id}/archive")
async def archive_knowledge_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive (deprecate) a knowledge document."""
    doc = db.query(KnowledgeDocument).filter(
        (KnowledgeDocument.id == doc_id) | (KnowledgeDocument.doc_id == doc_id)
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = KBDocStatus.DEPRECATED
    db.commit()
    return {"status": "archived", "doc_id": doc.doc_id}


@router.post("/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    organization_id: str = Form(""),
    department_id: str = Form(""),
    category: str = Form("General"),
    authority: str = Form("approved_faq"),
    document_type: str = Form("faq"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file (PDF, TXT, MD, JSON) and create a knowledge document or tenant dataset."""
    from app.services.trnding_importer import smart_import_json, run_reindex

    filename = file.filename or "untitled"
    content_bytes = await file.read()
    ext = os.path.splitext(filename)[1].lower()

    # Smart multi-schema JSON importer (detects organizations, departments, docs, FAQs, products, conversations)
    if ext == ".json":
        try:
            res = smart_import_json(content_bytes, filename, organization_id, db, current_user.full_name)
            # Rebuild index in background if knowledge docs were added
            if res.get("type") in ("knowledge_documents", "faqs", "products"):
                run_reindex()
                from app.main import rag_pipeline
                if rag_pipeline and hasattr(rag_pipeline, "retriever"):
                    rag_pipeline.retriever.reload()

            return {
                "status": "uploaded",
                "doc_id": res.get("type", "JSON"),
                "title": res["title"],
                "content_length": len(content_bytes),
                "message": res["message"],
                "type": res.get("type"),
                "count": res.get("count", 1),
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse JSON file: {str(e)}")

    if ext in (".txt", ".md", ".markdown"):
        text_content = content_bytes.decode("utf-8", errors="replace")
    elif ext == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc_pdf = fitz.open(stream=content_bytes, filetype="pdf")
            text_content = "\n\n".join(page.get_text() for page in doc_pdf)
            doc_pdf.close()
        except ImportError:
            text_content = "(PDF parsing requires PyMuPDF. Install: pip install PyMuPDF)"
    else:
        text_content = content_bytes.decode("utf-8", errors="replace")

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No text content extracted from file.")

    # Generate doc_id
    doc_id = f"KB-{uuid.uuid4().hex[:6].upper()}"
    title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()

    authority_map = {a.value: a for a in DocumentAuthority}
    doc_type_map = {t.value: t for t in DocumentType}

    doc = KnowledgeDocument(
        doc_id=doc_id,
        organization_id=organization_id or None,
        department_id=department_id or None,
        title=title,
        category=category,
        document_type=doc_type_map.get(document_type, DocumentType.FAQ),
        authority=authority_map.get(authority, DocumentAuthority.APPROVED_FAQ),
        content=text_content,
        keywords=_extract_keywords(text_content),
        version="1.0",
        status=KBDocStatus.ACTIVE,
        owner=current_user.full_name,
        source_filename=filename,
        effective_date=datetime.now(timezone.utc),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "status": "uploaded",
        "doc_id": doc.doc_id,
        "title": doc.title,
        "content_length": len(text_content),
        "message": "Document uploaded. Click 'Re-index' to include in search results.",
    }


@router.post("/load-trnding-pack")
async def load_trnding_pack_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """1-Click import of complete TRNDING tenant test pack (16 docs, 10 products, 20 FAQs, 9 support tickets)."""
    from app.services.trnding_importer import import_trnding_pack
    res = import_trnding_pack(db, current_user.full_name)
    from app.main import rag_pipeline
    if rag_pipeline and hasattr(rag_pipeline, "retriever"):
        rag_pipeline.retriever.reload()
    return {
        "status": "success",
        "organization_id": "org-trnding",
        "message": f"Successfully loaded TRNDING pack: {res['knowledge_docs_count']} knowledge docs, {res['products_count']} products, {res['faqs_count']} FAQs, {res['conversations_count']} conversations. Indices rebuilt!",
        **res,
    }


@router.post("/reindex")
async def reindex_knowledge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-build FAISS + BM25 indices from all active documents."""
    from app.services.trnding_importer import run_reindex
    success = run_reindex()
    from app.main import rag_pipeline
    if rag_pipeline and hasattr(rag_pipeline, "retriever"):
        rag_pipeline.retriever.reload()

    if success:
        return {"status": "success", "message": "Indices rebuilt and reloaded in memory."}
    return {"status": "error", "message": "Failed to rebuild indices."}


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search knowledge base using RAG pipeline."""
    from app.main import rag_pipeline

    if not rag_pipeline or not rag_pipeline.retriever.is_ready:
        raise HTTPException(status_code=503, detail="Knowledge index not built. Run build_index.py first.")

    result = rag_pipeline.process(
        request.query,
        top_k=request.top_k,
        organization_id=getattr(request, 'organization_id', None),
    )

    return [
        SearchResult(
            doc_id=c.get("faq_id", ""),
            title=c.get("title", ""),
            snippet=c.get("snippet", ""),
            relevance_score=c.get("relevance_score", 0),
            category=c.get("category", ""),
            version=c.get("version", ""),
        )
        for c in result["citations"]
    ]


def _extract_keywords(content: str) -> list:
    """Extract basic keywords from content."""
    important = ["api", "billing", "password", "security", "login", "team", "plan",
                  "subscription", "refund", "integration", "webhook", "export", "gdpr",
                  "sso", "oauth", "troubleshoot", "error", "upgrade", "cancel", "invoice"]
    found = [w for w in important if w in content.lower()]
    return found[:10]
