"""Smart importer for tenant test packs and multi-format JSON data.

Handles:
- TRNDING MVP RAG Test Pack (organization, departments, knowledge docs, products, FAQs, support conversations)
- Arbitrary JSON uploads (detects schema: organization, departments, knowledge, faqs, products, conversations)
- Auto index rebuild and RAG retriever reload
"""
import os
import re
import json
import uuid
import subprocess
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import (
    Organization, Department, KnowledgeDocument, Conversation, Message,
    KBDocStatus, DocumentAuthority, DocumentType, TicketStatus, TicketPriority,
    MessageSender, User
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TRNDING_PACK_DIR = os.path.join(PROJECT_ROOT, "data", "trnding_pack")


def _extract_keywords(content: str) -> list:
    important = [
        "api", "billing", "password", "security", "login", "team", "plan",
        "subscription", "refund", "integration", "webhook", "export", "netflix",
        "youtube", "adobe", "gemini", "zoom", "coursera", "delivery", "whatsapp",
        "guarantee", "replacement", "msme", "credentials", "unauthorized", "pricing"
    ]
    found = [w for w in important if w in content.lower()]
    # add capitalized tokens
    words = [w.strip(".,;:?!()[]\"'") for w in content.split() if len(w) > 3 and w.istitle()]
    for w in words[:5]:
        if w.lower() not in found:
            found.append(w.lower())
    return found[:12]


def run_reindex():
    """Trigger rebuild of FAISS and BM25 indices and reload in-memory retriever."""
    script = os.path.join(PROJECT_ROOT, "scripts", "build_index.py")
    venv_python = os.path.join(PROJECT_ROOT, "venv", "bin", "python")
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable

    try:
        res = subprocess.run(
            [python_cmd, script],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT_ROOT
        )
        # Reload running pipeline if available
        try:
            from app.main import rag_pipeline
            if rag_pipeline and hasattr(rag_pipeline, "retriever"):
                rag_pipeline.retriever.reload()
        except Exception as e:
            print(f"Retriever in-memory reload error: {e}")
        return res.returncode == 0
    except Exception as e:
        print(f"Error rebuilding index: {e}")
        return False


def import_trnding_pack(db: Session, current_user_name: str = "Admin") -> dict:
    """Import the complete TRNDING MVP pack into database and rebuild indices."""
    if not os.path.exists(TRNDING_PACK_DIR):
        # Fallback to Desktop if exists
        alt_dir = "/Users/adityatati/Desktop/trnding_resolveai_mvp"
        if os.path.exists(alt_dir):
            pack_dir = alt_dir
        else:
            raise FileNotFoundError(f"TRNDING pack not found in {TRNDING_PACK_DIR} or {alt_dir}")
    else:
        pack_dir = TRNDING_PACK_DIR

    results = {
        "organization": None,
        "departments_count": 0,
        "knowledge_docs_count": 0,
        "products_count": 0,
        "faqs_count": 0,
        "conversations_count": 0,
        "index_rebuilt": False,
    }

    # 1. Organization
    org_path = os.path.join(pack_dir, "organization.json")
    if os.path.exists(org_path):
        with open(org_path) as f:
            org_data = json.load(f)
            if isinstance(org_data, list) and len(org_data) > 0:
                org_data = org_data[0]
        org_id = org_data.get("organization_id", "org-trnding").replace("_", "-")
        org = db.query(Organization).filter((Organization.id == org_id) | (Organization.slug == "trnding")).first()
        if not org:
            org = Organization(
                id=org_id,
                name=org_data.get("name", "TRNDING"),
                slug="trnding",
                description=org_data.get("industry", "Digital subscriptions and software services"),
                is_active=True
            )
            db.add(org)
        else:
            org.id = org_id
            org.name = org_data.get("name", "TRNDING")
            org.description = org_data.get("industry", "Digital subscriptions and software services")
        db.commit()
        results["organization"] = org.name
    else:
        org_id = "org-trnding"

    # 2. Departments
    dept_path = os.path.join(pack_dir, "departments.json")
    if os.path.exists(dept_path):
        with open(dept_path) as f:
            depts = json.load(f)
        for d in depts:
            d_name = d.get("name", "Customer Support")
            d_slug = d_name.lower().replace(" ", "-")
            dept_id = f"dept-{org_id}-{d_slug}"
            existing = db.query(Department).filter(
                (Department.id == dept_id) |
                ((Department.organization_id == org_id) & (Department.name == d_name))
            ).first()
            if not existing:
                dept = Department(
                    id=dept_id,
                    organization_id=org_id,
                    name=d_name,
                    slug=d_slug,
                    is_active=True
                )
                db.add(dept)
                results["departments_count"] += 1
        db.commit()

    # 3. Knowledge Documents
    kdoc_path = os.path.join(pack_dir, "knowledge_documents.json")
    if os.path.exists(kdoc_path):
        with open(kdoc_path) as f:
            kdocs = json.load(f)
        for kd in kdocs:
            d_id = kd.get("document_id", f"KB-{uuid.uuid4().hex[:6].upper()}").replace("_", "-")
            existing = db.query(KnowledgeDocument).filter(
                (KnowledgeDocument.doc_id == d_id) |
                ((KnowledgeDocument.organization_id == org_id) & (KnowledgeDocument.title == kd["title"]))
            ).first()
            if existing:
                existing.content = kd["content"]
                existing.title = kd["title"]
                existing.category = kd.get("category", "General")
                existing.keywords = kd.get("keywords") or _extract_keywords(kd["content"])
                existing.source_url = kd.get("source_url")
                existing.status = KBDocStatus.ACTIVE
            else:
                doc = KnowledgeDocument(
                    doc_id=d_id,
                    organization_id=org_id,
                    title=kd["title"],
                    category=kd.get("category", "General"),
                    document_type=DocumentType.DOCUMENTATION,
                    authority=DocumentAuthority.OFFICIAL_DOCS,
                    content=kd["content"],
                    keywords=kd.get("keywords") or _extract_keywords(kd["content"]),
                    version=kd.get("version", "1.0"),
                    status=KBDocStatus.ACTIVE,
                    owner="TRNDING Team",
                    source_url=kd.get("source_url"),
                    source_filename="knowledge_documents.json",
                    effective_date=datetime.now(timezone.utc)
                )
                db.add(doc)
            results["knowledge_docs_count"] += 1
        db.commit()

    # 4. Products as Knowledge Docs
    prod_path = os.path.join(pack_dir, "products.json")
    if os.path.exists(prod_path):
        with open(prod_path) as f:
            prods = json.load(f)
        for p in prods:
            p_id = p.get("product_id", f"PROD-{uuid.uuid4().hex[:6].upper()}").replace("_", "-")
            p_name = p.get("name", "Product")
            p_price = p.get("price_inr", "N/A")
            p_duration = p.get("duration", "N/A")
            p_delivery = p.get("delivery", "30 minutes; up to 1 hour at peak")
            p_source = p.get("source_url", "https://trnding.in/")
            title = f"{p_name} — Subscription Plan & Pricing"
            content = (
                f"Product: {p_name}\n"
                f"Price: ₹{p_price}\n"
                f"Duration: {p_duration}\n"
                f"Delivery: {p_delivery}\n"
                f"Store Link: {p_source}\n"
                f"Overview: Genuine digital subscription from TRNDING India. Delivered via WhatsApp with replacement guarantee and 24/7 support."
            )
            existing = db.query(KnowledgeDocument).filter(
                (KnowledgeDocument.doc_id == p_id) |
                ((KnowledgeDocument.organization_id == org_id) & (KnowledgeDocument.title == title))
            ).first()
            if existing:
                existing.content = content
            else:
                doc = KnowledgeDocument(
                    doc_id=p_id,
                    organization_id=org_id,
                    title=title,
                    category="Products",
                    document_type=DocumentType.DOCUMENTATION,
                    authority=DocumentAuthority.OFFICIAL_DOCS,
                    content=content,
                    keywords=[p_name.lower(), "subscription", "price", "plan", "delivery"],
                    version="1.0",
                    status=KBDocStatus.ACTIVE,
                    owner="TRNDING Catalog",
                    source_url=p_source,
                    source_filename="products.json",
                    effective_date=datetime.now(timezone.utc)
                )
                db.add(doc)
            results["products_count"] += 1
        db.commit()

    # 5. FAQs as Knowledge Docs
    faq_path = os.path.join(pack_dir, "faqs.json")
    if os.path.exists(faq_path):
        with open(faq_path) as f:
            faqs = json.load(f)
        for faq in faqs:
            f_id = faq.get("faq_id", f"FAQ-{uuid.uuid4().hex[:6].upper()}").replace("_", "-")
            q = faq.get("question", "")
            a = faq.get("answer", "")
            title = f"FAQ: {q}"
            content = f"Question: {q}\n\nAnswer: {a}"
            existing = db.query(KnowledgeDocument).filter(
                (KnowledgeDocument.doc_id == f_id) |
                ((KnowledgeDocument.organization_id == org_id) & (KnowledgeDocument.title == title))
            ).first()
            if existing:
                existing.content = content
            else:
                doc = KnowledgeDocument(
                    doc_id=f_id,
                    organization_id=org_id,
                    title=title,
                    category="FAQ",
                    document_type=DocumentType.FAQ,
                    authority=DocumentAuthority.APPROVED_FAQ,
                    content=content,
                    keywords=_extract_keywords(f"{q} {a}"),
                    version="1.0",
                    status=KBDocStatus.ACTIVE,
                    owner="TRNDING Support",
                    source_filename="faqs.json",
                    effective_date=datetime.now(timezone.utc)
                )
                db.add(doc)
            results["faqs_count"] += 1
        db.commit()

    # 6. Support Conversations
    conv_path = os.path.join(pack_dir, "support_conversations.json")
    if os.path.exists(conv_path):
        with open(conv_path) as f:
            convs = json.load(f)
        for c in convs:
            c_id = c.get("conversation_id", f"conv-{uuid.uuid4().hex[:6]}").replace("_", "-")
            existing = db.query(Conversation).filter(Conversation.id == c_id).first()
            if not existing:
                msg_text = c.get("message", "")
                subj = msg_text[:75] + ("..." if len(msg_text) > 75 else "")
                conv = Conversation(
                    id=c_id,
                    organization_id=org_id,
                    customer_name=c.get("customer", "Customer"),
                    customer_email=f"{c.get('customer', 'cust').lower().replace(' ', '.')}@example.com",
                    subject=subj,
                    category="Support",
                    priority=TicketPriority.MEDIUM,
                    status=TicketStatus.NEW,
                )
                db.add(conv)
                db.flush()
                msg = Message(
                    id=f"msg-{c_id}-1",
                    conversation_id=c_id,
                    sender=MessageSender.CUSTOMER,
                    content=msg_text,
                )
                db.add(msg)
                results["conversations_count"] += 1
        db.commit()

    # 7. Rebuild indices
    rebuilt = run_reindex()
    results["index_rebuilt"] = rebuilt

    return results


def smart_import_json(
    content_bytes: bytes,
    filename: str,
    target_org_id: str,
    db: Session,
    current_user_name: str = "Admin",
) -> dict:
    """Intelligently inspect and parse JSON payload into appropriate tables."""
    try:
        data = json.loads(content_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON file: {e}")

    org_id = (target_org_id or "org-trnding").replace("_", "-")
    fname = filename.lower()

    # A: Organization definition
    if fname.startswith("organization") or (
        isinstance(data, (dict, list)) and
        (
            (isinstance(data, dict) and "organization_id" in data and "name" in data) or
            (isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "organization_id" in data[0] and "name" in data[0])
        )
    ):
        items = data if isinstance(data, list) else [data]
        created = []
        for it in items:
            oid = (it.get("organization_id") or f"org-{uuid.uuid4().hex[:6]}").replace("_", "-")
            name = it.get("name", "Organization")
            slug = it.get("slug") or name.lower().replace(" ", "-")
            desc = it.get("industry") or it.get("description", "")
            existing = db.query(Organization).filter((Organization.id == oid) | (Organization.slug == slug)).first()
            if existing:
                existing.name = name
                existing.description = desc
                created.append(existing.name)
            else:
                new_org = Organization(id=oid, name=name, slug=slug, description=desc, is_active=True)
                db.add(new_org)
                created.append(name)
        db.commit()
        return {
            "type": "organization",
            "title": f"Organization: {', '.join(created)}",
            "count": len(created),
            "message": f"Organization '{', '.join(created)}' imported and ready in tenant switcher!",
        }

    # B: Departments definition
    if fname.startswith("department") or (
        isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "department_id" in data[0]
    ):
        items = data if isinstance(data, list) else [data]
        created = []
        for it in items:
            d_name = it.get("name", "Support")
            d_slug = d_name.lower().replace(" ", "-")
            dept_id = f"dept-{org_id}-{d_slug}"
            existing = db.query(Department).filter(
                (Department.id == dept_id) |
                ((Department.organization_id == org_id) & (Department.name == d_name))
            ).first()
            if not existing:
                dept = Department(
                    id=dept_id,
                    organization_id=org_id,
                    name=d_name,
                    slug=d_slug,
                    is_active=True
                )
                db.add(dept)
                created.append(d_name)
        db.commit()
        return {
            "type": "departments",
            "title": f"{len(created)} Departments",
            "count": len(created),
            "message": f"Imported {len(created)} departments: {', '.join(created)}",
        }

    # C: Support Conversations
    if fname.startswith("support") or (
        isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "customer" in data[0] and "message" in data[0]
    ):
        items = data if isinstance(data, list) else [data]
        count = 0
        for it in items:
            c_id = (it.get("conversation_id") or f"conv-{uuid.uuid4().hex[:6]}").replace("_", "-")
            existing = db.query(Conversation).filter(Conversation.id == c_id).first()
            if not existing:
                msg_text = it.get("message", "")
                subj = msg_text[:75] + ("..." if len(msg_text) > 75 else "")
                conv = Conversation(
                    id=c_id,
                    organization_id=org_id,
                    customer_name=it.get("customer", "Customer"),
                    customer_email=f"{it.get('customer', 'cust').lower().replace(' ', '.')}@example.com",
                    subject=subj,
                    category="Support",
                    priority=TicketPriority.MEDIUM,
                    status=TicketStatus.NEW,
                )
                db.add(conv)
                db.flush()
                msg = Message(
                    id=f"msg-{c_id}-1",
                    conversation_id=c_id,
                    sender=MessageSender.CUSTOMER,
                    content=msg_text,
                )
                db.add(msg)
                count += 1
        db.commit()
        return {
            "type": "conversations",
            "title": f"{count} Support Conversations",
            "count": count,
            "message": f"Successfully imported {count} customer conversations into Inbox!",
        }

    # D: Products
    if fname.startswith("product") or (
        isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and ("price_inr" in data[0] or "price" in data[0])
    ):
        items = data if isinstance(data, list) else [data]
        count = 0
        for p in items:
            p_id = (p.get("product_id") or f"PROD-{uuid.uuid4().hex[:6].upper()}").replace("_", "-")
            p_name = p.get("name", "Product")
            p_price = p.get("price_inr", p.get("price", "N/A"))
            p_duration = p.get("duration", "N/A")
            p_delivery = p.get("delivery", "30 minutes")
            p_source = p.get("source_url", "")
            title = f"{p_name} — Subscription Plan & Pricing"
            content = (
                f"Product: {p_name}\nPrice: ₹{p_price}\nDuration: {p_duration}\n"
                f"Delivery: {p_delivery}\nStore: {p_source}\n"
                f"Details: Genuine digital subscription with replacement guarantee."
            )
            existing = db.query(KnowledgeDocument).filter(
                (KnowledgeDocument.doc_id == p_id) |
                ((KnowledgeDocument.organization_id == org_id) & (KnowledgeDocument.title == title))
            ).first()
            if existing:
                existing.content = content
            else:
                doc = KnowledgeDocument(
                    doc_id=p_id,
                    organization_id=org_id,
                    title=title,
                    category="Products",
                    document_type=DocumentType.DOCUMENTATION,
                    authority=DocumentAuthority.OFFICIAL_DOCS,
                    content=content,
                    keywords=[p_name.lower(), "subscription", "price", "plan"],
                    version="1.0",
                    status=KBDocStatus.ACTIVE,
                    owner=current_user_name,
                    source_url=p_source,
                    source_filename=filename,
                    effective_date=datetime.now(timezone.utc)
                )
                db.add(doc)
            count += 1
        db.commit()
        return {
            "type": "products",
            "title": f"{count} Products",
            "count": count,
            "message": f"Imported {count} products into knowledge base!",
        }

    # E: FAQs
    if fname.startswith("faq") or (
        isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "question" in data[0] and "answer" in data[0]
    ):
        items = data if isinstance(data, list) else [data]
        count = 0
        for faq in items:
            f_id = (faq.get("faq_id") or f"FAQ-{uuid.uuid4().hex[:6].upper()}").replace("_", "-")
            q = faq.get("question", "")
            a = faq.get("answer", "")
            title = f"FAQ: {q}"
            content = f"Question: {q}\n\nAnswer: {a}"
            existing = db.query(KnowledgeDocument).filter(
                (KnowledgeDocument.doc_id == f_id) |
                ((KnowledgeDocument.organization_id == org_id) & (KnowledgeDocument.title == title))
            ).first()
            if existing:
                existing.content = content
            else:
                doc = KnowledgeDocument(
                    doc_id=f_id,
                    organization_id=org_id,
                    title=title,
                    category="FAQ",
                    document_type=DocumentType.FAQ,
                    authority=DocumentAuthority.APPROVED_FAQ,
                    content=content,
                    keywords=_extract_keywords(f"{q} {a}"),
                    version="1.0",
                    status=KBDocStatus.ACTIVE,
                    owner=current_user_name,
                    source_filename=filename,
                    effective_date=datetime.now(timezone.utc)
                )
                db.add(doc)
            count += 1
        db.commit()
        return {
            "type": "faqs",
            "title": f"{count} FAQs",
            "count": count,
            "message": f"Imported {count} FAQs into knowledge base!",
        }

    # F: Knowledge Documents list
    if (
        isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and
        ("title" in data[0] and "content" in data[0])
    ):
        count = 0
        for item in data:
            d_id = (item.get("document_id") or item.get("id") or f"KB-{uuid.uuid4().hex[:6].upper()}").replace("_", "-")
            d_org = (item.get("organization_id") or org_id).replace("_", "-")
            d_title = item.get("title", "Untitled Document")
            d_content = item.get("content", "")
            d_cat = item.get("category", "General")
            existing = db.query(KnowledgeDocument).filter(
                (KnowledgeDocument.doc_id == d_id) |
                ((KnowledgeDocument.organization_id == d_org) & (KnowledgeDocument.title == d_title))
            ).first()
            if existing:
                existing.content = d_content
                existing.title = d_title
                existing.category = d_cat
                existing.keywords = item.get("keywords") or _extract_keywords(d_content)
                existing.source_url = item.get("source_url")
            else:
                doc = KnowledgeDocument(
                    doc_id=d_id,
                    organization_id=d_org,
                    title=d_title,
                    category=d_cat,
                    document_type=DocumentType.DOCUMENTATION,
                    authority=DocumentAuthority.OFFICIAL_DOCS,
                    content=d_content,
                    keywords=item.get("keywords") or _extract_keywords(d_content),
                    version=item.get("version", "1.0"),
                    status=KBDocStatus.ACTIVE,
                    owner=current_user_name,
                    source_url=item.get("source_url"),
                    source_filename=filename,
                    effective_date=datetime.now(timezone.utc)
                )
                db.add(doc)
            count += 1
        db.commit()
        return {
            "type": "knowledge_documents",
            "title": f"{count} Knowledge Documents",
            "count": count,
            "message": f"Imported {count} knowledge documents!",
        }

    # G: Fallback generic JSON (single doc)
    content_text = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    doc_id = f"KB-{uuid.uuid4().hex[:6].upper()}"
    title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
    doc = KnowledgeDocument(
        doc_id=doc_id,
        organization_id=org_id,
        title=title,
        category="General",
        document_type=DocumentType.FAQ,
        authority=DocumentAuthority.APPROVED_FAQ,
        content=content_text,
        keywords=_extract_keywords(content_text),
        version="1.0",
        status=KBDocStatus.ACTIVE,
        owner=current_user_name,
        source_filename=filename,
        effective_date=datetime.now(timezone.utc)
    )
    db.add(doc)
    db.commit()
    return {
        "type": "single_document",
        "title": title,
        "count": 1,
        "message": f"Document '{title}' created from JSON.",
    }
