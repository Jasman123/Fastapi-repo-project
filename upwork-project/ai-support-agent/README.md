# 🤖 AI Customer Support Agent

**Multi-agent pipeline built with LangChain · LangGraph · FastAPI · GCP Cloud Run**

A production-grade AI system that classifies support tickets, generates answers, and escalates when confidence is too low — all orchestrated by a LangGraph state machine.

---

## 📊 Why This Project

Based on Upwork's 2026 In-Demand Skills Report, this single project covers the top 4 fastest-growing AI skill categories:

| Upwork Skill Category | YoY Growth | How This Project Demonstrates It |
|---|---|---|
| AI Integration | +178% | LangChain + Anthropic API integration |
| ML Engineering | +109% | LangGraph state machine, classification pipeline |
| Automation | +98% | Multi-node automated ticket processing |
| AI Chatbot Dev | +71% | Conversational response generation + QA gate |

---

## 🏗 Project Structure

```
ai-support-agent/
├── app/
│   ├── main.py                  # FastAPI application + middleware
│   ├── config.py                # Pydantic settings (env-based)
│   ├── agents/
│   │   └── support_graph.py     # ⭐ LangGraph multi-agent pipeline
│   ├── api/
│   │   └── routes.py            # REST endpoints
│   ├── models/
│   │   └── schemas.py           # Pydantic v2 request/response models
│   └── services/
│       └── llm_service.py       # LLM abstraction layer (Anthropic SDK)
├── tests/
│   └── test_support_agent.py    # Pytest suite (mocked, runs offline)
├── scripts/
│   ├── demo.py                  # Rich terminal demo (no API key needed)
│   └── deploy_gcp.sh            # GCP Cloud Run deployment script
├── Dockerfile                   # Multi-stage build for Cloud Run
├── requirements.txt
└── README.md
```

---

## ⚙️ LangGraph Pipeline

```
[START]
   │
   ▼
classify_ticket          ← Node 1: LLM assigns category + confidence score
   │
   ├─ conf < 0.55 ──► escalate_ticket   ← Node 3: routes to human queue
   │
   └─ conf ≥ 0.55 ──► generate_answer   ← Node 2: LLM drafts reply
                            │
                            ▼
                       review_answer      ← Node 4: QA quality gate
                            │
                   ┌────────┴──────────┐
               pass│                  │fail
                   ▼                  ▼
                 [END]         escalate_ticket
```

---

## 🚀 Installation

### 1. Clone & enter directory
```bash
git clone https://github.com/yourname/ai-support-agent.git
cd ai-support-agent
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

**.env.example:**
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_MODEL=claude-3-5-haiku-20241022
ESCALATION_CONFIDENCE_THRESHOLD=0.55
APP_ENV=development
```

### 5. Run the demo (no API key needed)
```bash
python scripts/demo.py
```

### 6. Run tests (also offline)
```bash
pytest tests/ -v
```

### 7. Start the API server
```bash
uvicorn app.main:app --reload
# → http://localhost:8000/docs (Swagger UI)
```

---

## 🧪 API Usage

### Single ticket
```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "customer_name": "Sarah Chen",
    "message": "I was charged twice this month. Please refund.",
    "priority": "high"
  }'
```

**Response:**
```json
{
  "ticket_id": "TKT-001",
  "action": "answer",
  "category": "billing",
  "confidence": 0.94,
  "answer": "Hi Sarah, I'm so sorry about the duplicate charge! ...",
  "escalation_reason": null,
  "node_trace": ["classify_ticket", "generate_answer", "review_answer"],
  "processing_time_ms": 1823.4
}
```

### Batch processing
```bash
curl -X POST http://localhost:8000/api/v1/tickets/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"ticket_id":"TKT-001","customer_name":"Alice","message":"Refund please","priority":"high"},
    {"ticket_id":"TKT-002","customer_name":"Bob","message":"App crashes","priority":"medium"}
  ]'
```

---

## ☁️ Deploy to GCP Cloud Run

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy (builds image + deploys in one command)
export ANTHROPIC_API_KEY=sk-ant-your-key
export GCP_PROJECT_ID=your-project-id
bash scripts/deploy_gcp.sh
```

Cost estimate: ~$0 for demo traffic (Cloud Run free tier: 2M requests/month).

---

## 📋 Key Design Decisions

| Decision | Why |
|---|---|
| LangGraph for orchestration | Explicit state machine — debuggable, auditable, extendable |
| Pydantic v2 models | Type safety + auto-validation + OpenAPI docs for free |
| LLM abstraction layer | Swap Claude → GPT-4 → Gemini without touching agent code |
| QA review node | Two-pass LLM quality gate prevents bad answers reaching customers |
| Confidence threshold escalation | Graceful degradation — uncertain → human, not wrong AI answer |

---

## 🧩 Extension Ideas (for client projects)

- **RAG integration** — add a `retrieve_kb` node that pulls from a vector store before generating
- **Slack / email escalation** — real webhook calls in `escalate_ticket`
- **Streaming responses** — FastAPI `StreamingResponse` + LangChain streaming
- **Analytics dashboard** — persist `AgentState` to BigQuery, visualise with Looker
- **Multi-language** — add a `translate` node before classify, route back after answer

---

## 🛠 Stack

- **LangChain** `>=0.3` — LLM abstraction, prompt management
- **LangGraph** `>=0.2` — stateful multi-agent orchestration
- **FastAPI** `>=0.115` — async REST API, auto OpenAPI docs
- **Anthropic Claude** — `claude-3-5-haiku` for speed + cost efficiency
- **Pydantic v2** — schema validation and settings
- **GCP Cloud Run** — serverless container deployment
- **Pytest** — offline test suite with mocked LLM calls
