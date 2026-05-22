# ResearchAgent

LangGraph-powered automated research and report generation.  
FastAPI backend · GPT-4o · Tavily Search · HTML/CSS frontend · Docker ready.

## Project Structure

```
research-agent/
├── app/
│   ├── agent/
│   │   ├── graph.py        ← LangGraph StateGraph + conditional routing
│   │   └── nodes.py        ← 5 async nodes (plan → search → extract → synthesize → report)
│   ├── tools/
│   │   ├── llm.py          ← LLM factory: OpenAI GPT-4o or Vertex AI Gemini
│   │   └── search.py       ← Tavily primary + DuckDuckGo fallback
│   ├── utils/
│   │   └── config.py       ← Pydantic v2 Settings (env-driven)
│   └── main.py             ← FastAPI app: POST /research, GET /health
├── frontend/
│   └── index.html          ← Single-file HTML/CSS/JS UI
├── tests/
│   └── test_agent.py       ← 8 tests, fully mocked (no API calls needed)
├── .env.example
├── .gitignore
├── Dockerfile              ← Multi-stage build, non-root user
├── .dockerignore
├── requirements.txt
└── README.md
```

## Quickstart

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env: add OPENAI_API_KEY and TAVILY_API_KEY

# 2. Install and run backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Serve frontend
python -m http.server 3000 --directory frontend
# Open http://localhost:3000

# 4. Run tests (no API keys needed)
pytest tests/ -v
```

## API

### POST /research
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d '{"topic": "Impact of AI agents on enterprise software 2025"}'
```

Response:
```json
{
  "job_id": "uuid",
  "topic": "...",
  "report_markdown": "# Report...",
  "search_queries": ["query 1", "query 2", "query 3", "query 4"],
  "sources_count": 8,
  "elapsed_seconds": 18.4,
  "status": "completed"
}
```

### GET /health
```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "1.0.0"}
```

## Docker

```bash
docker build -t research-agent .
docker run -p 8000:8080 --env-file .env research-agent
```

## Agent Pipeline

```
START
  └─► plan_research     GPT-4 generates 4 focused search queries
        └─► search_web  Executes each query (Tavily / DuckDuckGo) — loops until done
              └─► extract_data    Structures + scores results with GPT-4
                    └─► synthesize         Executive narrative summary
                          └─► generate_report    Full Markdown report
                                └─► END
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `vertex` |
| `OPENAI_API_KEY` | — | Required for OpenAI |
| `OPENAI_MODEL` | `gpt-4o` | Model name |
| `TAVILY_API_KEY` | — | Leave blank → DuckDuckGo fallback |
| `API_KEY` | `dev-key-change-me` | Frontend → backend auth |
| `GCP_PROJECT` | — | Required for Vertex AI |