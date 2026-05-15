# Ingest
curl -X POST http://localhost:8000/ingest \
  -F "file=@rag-document/project-4/uploads/dummy_contract.pdf"
  

# Ask — RAG question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the document say about X?", "session_id": "u1"}'

# Ask — conversational (routes to direct_llm, skips Milvus)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello, how are you?", "session_id": "u1"}'

# Follow-up — uses chat history
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Can you explain that in simpler terms?", "session_id": "u1"}'

# List documents
curl http://localhost:8000/documents

# Delete a document
curl -X DELETE http://localhost:8000/documents/your_doc.pdf