# Bot-ए-rar

**Enterprise Multi-Tenant AI Support Copilot**

> Grounded answers. Faster support. Human control.

Bot-ए-rar is an enterprise AI customer support copilot that helps human agents understand customer issues, retrieve verified knowledge, generate evidence-based response drafts, and maintain full human oversight across multi-tenant organizations.

Built for the Microsoft Hackathon — runs 100% locally on open-source technology.

---

## Key Principles

- **AI Assists. Humans Decide.** — Every AI-generated response requires explicit human approval before sending.
- **Grounded, Not Fabricated** — All answers are backed by verified knowledge base citations with measurable confidence scores.
- **Transparent AI** — Full audit trail, confidence breakdowns, and knowledge gap detection.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Login · Inbox · Draft Workspace · Knowledge · Analytics │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│  Auth · Conversations · Drafts · Knowledge · Analytics   │
├──────────────────────┬──────────────────────────────────┤
│   Support Copilot    │   LLM Service                    │
│   (Orchestrator)     │   (Ollama / Fallback)            │
├──────────────────────┴──────────────────────────────────┤
│                    RAG Pipeline                          │
│  FAISS (Dense) + BM25 (Sparse) → RRF Fusion → Reranker │
├─────────────────────────────────────────────────────────┤
│              SQLite + Knowledge Base                     │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer         | Technology                            |
|---------------|---------------------------------------|
| Frontend      | React 19, TypeScript, Vite, Tailwind  |
| Backend       | FastAPI, SQLAlchemy, SQLite            |
| LLM           | Qwen2.5-1.5B via Ollama (local)       |
| Embeddings    | all-MiniLM-L6-v2 (SentenceTransformers)|
| Reranker      | cross-encoder/ms-marco-MiniLM-L-6-v2  |
| Dense Search  | FAISS                                  |
| Sparse Search | BM25 (rank_bm25)                       |
| State         | Zustand                                |
| Auth          | JWT + bcrypt                           |
| Fine-tuning   | LoRA/QLoRA via PEFT + TRL              |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (optional — for LLM inference)

### 1. Backend Setup

```bash
cd resolveai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment config
cp .env.example .env

# Build search indices (downloads embedding model on first run)
python scripts/build_index.py

# Seed demo data
cd backend && python ../scripts/seed_demo.py

# Start backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd resolveai/frontend

# Install dependencies
npm install

# Start dev server (proxies API to backend)
npm run dev
```

### 3. (Optional) LLM Setup

```bash
# Install Ollama
brew install ollama

# Pull the model
ollama pull qwen2.5:1.5b

# Ollama runs automatically in background
```

### 4. Open in Browser

Navigate to `http://localhost:5173`

**Demo Login:** `sarah@resolveai.demo` / `demo123`

## Demo Scenarios

| # | Scenario                  | Conversation | What to Demo                                |
|---|---------------------------|-------------|---------------------------------------------|
| 1 | Password Reset            | conv-001    | High confidence, verified citations         |
| 2 | Billing Knowledge Gap     | conv-002    | Gap detection, recommended documentation    |
| 3 | Security Escalation       | conv-003    | Auto-escalation, security team routing      |
| 4 | Multi-Intent Request      | conv-004    | Multiple topics handled in one response     |
| 5 | Prompt Injection          | conv-005    | Injection blocked, safe redirect            |

## Feature Map

### Core AI Pipeline
- ✅ Hybrid retrieval (FAISS dense + BM25 sparse)
- ✅ Reciprocal Rank Fusion (RRF) score merging
- ✅ Cross-encoder reranking
- ✅ Section-aware document chunking
- ✅ Grounding confidence (4 measurable signals, not LLM self-assessment)
- ✅ Knowledge gap detection
- ✅ Citation generation with source verification
- ✅ Prompt injection detection

### Human-in-the-Loop
- ✅ Draft review workspace
- ✅ Edit drafts before sending
- ✅ Approve / Reject / Regenerate workflow
- ✅ Edit distance tracking
- ✅ Full audit trail

### Escalation & Safety
- ✅ Auto-escalation for security/legal/PII concerns
- ✅ Prompt injection detection
- ✅ Team routing recommendations

### Knowledge Management
- ✅ 20-article CloudDesk knowledge base
- ✅ Knowledge base browser with search
- ✅ Knowledge gap tracking with impact scoring
- ✅ Recommended actions for gap resolution

### Analytics & Evaluation
- ✅ Real-time analytics from database
- ✅ RAG metrics (Recall@1/3/5, MRR)
- ✅ Model metrics (Groundedness, Citation Accuracy)
- ✅ Confidence distribution tracking
- ✅ Approval/rejection rate monitoring

### Enterprise Features
- ✅ JWT authentication
- ✅ Role-based access (Agent/Admin/Manager)
- ✅ Dark mode
- ✅ Command palette (⌘K)
- ✅ System health monitoring
- ✅ Fine-tuning pipeline (LoRA/QLoRA)

## Project Structure

```
resolveai/
├── backend/
│   └── app/
│       ├── api/routes/     # REST endpoints
│       ├── core/           # Configuration
│       ├── db/             # Database
│       ├── llm/            # LLM service
│       ├── models/         # ORM models
│       ├── schemas/        # Pydantic schemas
│       ├── security/       # Auth & injection detection
│       ├── services/       # Copilot orchestrator
│       └── main.py         # FastAPI app
├── frontend/
│   └── src/
│       ├── components/     # Toast, CommandPalette
│       ├── layouts/        # App shell
│       ├── pages/          # All pages
│       ├── services/       # API layer
│       ├── stores/         # Zustand state
│       └── types/          # TypeScript types
├── rag/
│   ├── embeddings.py       # SentenceTransformer encoding
│   ├── vector_store.py     # FAISS operations
│   ├── bm25.py             # BM25 sparse search
│   ├── reranker.py         # Cross-encoder reranking
│   ├── retriever.py        # Hybrid retrieval + RRF
│   └── pipeline.py         # Full RAG pipeline
├── data/
│   └── knowledge_base/     # CloudDesk KB articles
├── scripts/
│   ├── build_index.py      # Build FAISS + BM25 indices
│   ├── seed_demo.py        # Seed demo data
│   └── train_lora.py       # Fine-tuning pipeline
└── models/
    └── adapters/           # Fine-tuned LoRA adapters
```

## License

MIT
