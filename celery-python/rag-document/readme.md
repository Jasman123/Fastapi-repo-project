# Mini RAG API

FastAPI + Celery + ChromaDB + OpenAI — async document ingestion and RAG query.

---

## Architecture

```
Client → FastAPI → Celery (Redis broker) → OpenAI Embeddings → ChromaDB
                ↓
           GET /tasks/{id}  ←  poll status
                ↓
        POST /chat/query → OpenAI Chat → answer
```

---

## Prerequisites

- Python 3.10+
- Docker (for Redis)
- OpenAI API key

---

## Step 1 — Clone and enter the project

```bash
cd celery-python/rag-document
```

---

## Step 2 — Set up environment variables

Copy the example and fill in your OpenAI key:

```bash
cp .env .env.local
```

Edit `.env` and set:

```env
OPENAI_API_KEY=sk-...your-key-here...
REDIS_URL=redis://localhost:6379/0
CHROMA_PERSIST_DIR=./chroma_data
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

---

## Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
pip install "httpx>=0.23.0,<0.28.0"   # pin for openai 1.54 compatibility
```

> **Why the httpx pin?** `httpx 0.28` dropped the `proxies` argument that `openai 1.54.0` relies on internally. Pinning to `0.27.x` resolves this.

---

## Step 4 — Start Redis

```bash
docker compose up -d
```

Verify it is running:

```bash
docker exec rag-redis redis-cli ping
# Expected: PONG
```

---

## Step 5 — Start the Celery worker

Open a new terminal:

```bash
cd celery-python/rag-document
celery -A app.celery_app worker --loglevel=info
```

You should see:

```
[tasks]
  . app.tasks.ingest_document

[...] celery@hostname ready.
```

---

## Step 6 — Start the FastAPI server

Open another terminal:

```bash
cd celery-python/rag-document
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:

```
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

---

## Step 7 — Test the API

### Health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status": "ok"}
```

---

### Ingest a document

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "doc-001",
    "title": "Intro to AI",
    "content": "Artificial intelligence is the simulation of human intelligence by machines. Machine learning is a subset of AI that enables systems to learn from data without being explicitly programmed."
  }'
```

Expected (202 Accepted):

```json
{
  "task_id": "abc123-...",
  "doc_id": "doc-001",
  "status": "queued",
  "message": "Document ingestion started..."
}
```

---

### Poll task status

Copy the `task_id` from the previous response:

```bash
curl http://localhost:8000/tasks/<task_id>
```

Poll until `status` is `SUCCESS`:

```json
{
  "task_id": "abc123-...",
  "status": "SUCCESS",
  "result": {
    "doc_id": "doc-001",
    "status": "sucess",
    "chunks_stored": 1,
    "embedding_model": "text-embedding-3-small"
  },
  "error": null
}
```

Possible status values: `PENDING` → `STARTED` → `SUCCESS` / `FAILURE`

---

### Query the RAG

After at least one document is ingested:

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "top_k": 3
  }'
```

Expected:

```json
{
  "question": "What is machine learning?",
  "answer": "Machine learning is a subset of AI that enables systems to learn from data... (Source: doc-001)",
  "sources": [
    {
      "doc_id": "doc-001",
      "chunk_index": 0,
      "text": "...",
      "similarity_score": 0.548
    }
  ],
  "model": "gpt-4o-mini"
}
```

---

## Interactive API docs

Open in browser: [http://localhost:8000/docs](http://localhost:8000/docs)

Swagger UI lets you test all endpoints without curl.

---

## Stop everything

```bash
# Stop FastAPI and Celery with Ctrl+C in their terminals

# Stop Redis
docker compose down
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` on Redis | Docker not running | `docker compose up -d` |
| `Client.__init__() proxies` error | httpx 0.28 incompatible | `pip install "httpx<0.28"` |
| Task stuck in `PENDING` | Celery worker not running | Start worker (Step 5) |
| `FAILURE` on ingest | Bad OpenAI key | Check `OPENAI_API_KEY` in `.env` |
| `I don't have any documents` | No docs ingested yet | Run ingest first (Step 7) |
