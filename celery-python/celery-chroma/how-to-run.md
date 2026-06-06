# 1. Buat folder project
mkdir ai-tasks && cd ai-tasks
mkdir -p app chroma_data

# 2. Buat semua file di atas
# (copy paste satu per satu)

# 3. Install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Start Redis
docker compose up -d

# 5. Start Celery Worker (Terminal 1)
celery -A app.celery_app worker --loglevel=info

# 6. Start FastAPI (Terminal 2)
uvicorn main:app --reload --port 8000

# 7. Test di Terminal 3
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "doc_001",
    "title": "Belajar Python",
    "content": "Python adalah bahasa pemrograman yang mudah dipelajari. Python diciptakan oleh Guido van Rossum. Python sangat populer untuk AI dan data science."
  }'

# Ambil task_id dari response, lalu:
curl http://localhost:8000/api/tasks/<task_id>

# Setelah SUCCESS, tanya:
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Siapa yang menciptakan Python?"}'