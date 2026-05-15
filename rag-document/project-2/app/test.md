# Ingest a PDF
curl -X POST http://localhost:8000/ingest \
  -F "file=@rag-document/project-2/document/dummy_contract.pdf"

# Ask a question — now returns sources too
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "tell me about the document?"}'

# Check status
curl http://localhost:8000/status