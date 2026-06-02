# 1. Start Redis
docker compose up -d

# 2. Start Celery Worker
celery -A app.core.celery worker --loglevel=info --concurrency=4

# Worker output seharusnya:
# [tasks]
#   . app.tasks.chat_tasks.ask_llm
#   . app.tasks.chat_tasks.summarize
#   . app.tasks.chat_tasks.process_batch
#   . app.tasks.document_tasks.ingest_text
#   . app.tasks.document_tasks.ingest_pdf

# 3. Start FastAPI
uvicorn main:app --reload --port 8000