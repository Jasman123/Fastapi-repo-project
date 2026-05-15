# Ingest
curl -X POST http://localhost:8000/ingest \
  -F "file=@rag-document/project-3/uploads/dummy_contract.pdf"

# Ask — first question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "session_id": "user123"}'

# Ask — follow-up (uses conversation history)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Can you elaborate on that?", "session_id": "user123"}'

# Clear session memory
curl -X DELETE http://localhost:8000/sessions/user123