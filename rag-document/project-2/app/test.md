# Ingest a PDF
curl -X POST http://localhost:8000/ingest \
  -F "file=@your_document.pdf"

# Ask a question — now returns sources too
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of this document?"}'

# Check status
curl http://localhost:8000/status