# Step 1 — create a test document
echo "FastAPI is a modern Python web framework. 
It supports async natively and is built on Starlette.
FastAPI automatically generates OpenAPI documentation.
It uses Pydantic for data validation.
FastAPI is one of the fastest Python frameworks available." > test.txt

# Step 2 — ingest it
curl -X POST http://localhost:8000/ingest \
  -F "file=@test.txt"

# Expected response:
# {"filename":"test.txt","chunks":1,"message":"Ingested 1 chunks into vector DB"}

# Step 3 — ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is FastAPI built on?"}'

# Expected response:
# {"answer":"FastAPI is built on Starlette.","chunks_used":1}

# Step 4 — check status
curl http://localhost:8000/

###