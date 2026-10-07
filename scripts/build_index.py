#!/usr/bin/env python3
"""Build FAISS and BM25 indices from database knowledge documents.

V2: Reads from database (multi-tenant), includes organization_id + authority
    in chunk metadata for tenant-aware retrieval.

Usage:
    python scripts/build_index.py
"""
import json
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chunk_document(doc: dict, chunk_size: int = 512, overlap: int = 50) -> list:
    """Section-aware chunking with overlap."""
    content = doc["content"]
    doc_id = doc["id"]
    title = doc["title"]
    category = doc.get("category", "")
    version = doc.get("version", "")
    updated_at = doc.get("updated_at", "")
    organization_id = doc.get("organization_id", "")
    department_id = doc.get("department_id", "")
    authority = doc.get("authority", "approved_faq")

    sections = re.split(r"\n\n+", content)

    chunks = []
    current_chunk = ""
    chunk_idx = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(current_chunk) + len(section) > chunk_size and current_chunk:
            chunks.append({
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_chunk_{chunk_idx}",
                "title": title,
                "category": category,
                "version": version,
                "updated_at": updated_at,
                "organization_id": organization_id,
                "department_id": department_id,
                "authority": authority,
                "content": current_chunk.strip(),
                "text": current_chunk.strip(),
            })
            chunk_idx += 1
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else ""
            current_chunk = overlap_text + "\n" + section
        else:
            current_chunk += "\n" + section if current_chunk else section

    if current_chunk.strip():
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_chunk_{chunk_idx}",
            "title": title,
            "category": category,
            "version": version,
            "updated_at": updated_at,
            "organization_id": organization_id,
            "department_id": department_id,
            "authority": authority,
            "content": current_chunk.strip(),
            "text": current_chunk.strip(),
        })

    return chunks


def load_documents_from_db():
    """Load knowledge documents from the database."""
    from app.db.database import SessionLocal
    from app.models.models import KnowledgeDocument, KBDocStatus

    db = SessionLocal()
    try:
        docs = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.status == KBDocStatus.ACTIVE
        ).all()

        documents = []
        for doc in docs:
            documents.append({
                "id": doc.doc_id,
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "version": doc.version,
                "updated_at": doc.updated_at.strftime("%Y-%m-%d") if doc.updated_at else "",
                "organization_id": doc.organization_id or "",
                "department_id": doc.department_id or "",
                "authority": doc.authority.value if doc.authority else "approved_faq",
            })
        return documents
    finally:
        db.close()


def load_documents_from_json():
    """Fallback: Load from JSON file."""
    kb_path = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "knowledge_base.json")
    if not os.path.exists(kb_path):
        return []
    with open(kb_path, "r") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("ResolveAI — Knowledge Base Index Builder (V2)")
    print("=" * 60)

    # Try loading from database first, fall back to JSON
    print("\nLoading knowledge documents...")
    try:
        documents = load_documents_from_db()
        print(f"Loaded {len(documents)} documents from database")
    except Exception as e:
        print(f"Database unavailable ({e}), falling back to JSON...")
        documents = load_documents_from_json()
        print(f"Loaded {len(documents)} documents from JSON")

    if not documents:
        print("ERROR: No documents found. Run seed_demo.py first.")
        sys.exit(1)

    # Show per-org breakdown
    orgs = {}
    for d in documents:
        org = d.get("organization_id", "unknown") or "unknown"
        orgs[org] = orgs.get(org, 0) + 1
    for org, count in orgs.items():
        print(f"  {org}: {count} documents")

    # Chunk documents
    print("\nChunking documents...")
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")

    # Build embeddings
    print("\nGenerating embeddings (this may take a moment on first run)...")
    from rag.embeddings import encode_texts

    texts = [c["content"] for c in all_chunks]
    embeddings = encode_texts(texts)
    dim = embeddings.shape[1]
    print(f"Generated embeddings: shape={embeddings.shape}, dim={dim}")

    # Build FAISS index
    print("\nBuilding FAISS index...")
    from rag.vector_store import FAISSVectorStore

    index_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    os.makedirs(index_dir, exist_ok=True)

    faiss_path = os.path.join(index_dir, "faiss_index")
    vector_store = FAISSVectorStore(faiss_path, dimension=dim)
    vector_store.build(embeddings, all_chunks)
    vector_store.save()
    print(f"FAISS index saved: {vector_store.count} vectors")

    # Build BM25 index
    print("\nBuilding BM25 index...")
    from rag.bm25 import BM25Search

    bm25_path = os.path.join(index_dir, "bm25_index.pkl")
    bm25 = BM25Search(bm25_path)
    bm25.build(texts, all_chunks)
    bm25.save()
    print(f"BM25 index saved: {bm25.count} documents")

    print("\n" + "=" * 60)
    print("Index building complete!")
    print(f"  Documents:  {len(documents)}")
    print(f"  Chunks:     {len(all_chunks)}")
    print(f"  FAISS:      {vector_store.count} vectors ({dim}d)")
    print(f"  BM25:       {bm25.count} documents")
    for org, count in orgs.items():
        print(f"  Org [{org}]: {count} docs indexed")
    print(f"  Index dir:  {index_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
