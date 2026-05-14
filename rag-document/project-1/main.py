from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import chromadb
import os

load_dotenv()


app = FastAPI(title="Simple RAG API")
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chromadb_client = chromadb.Client()

collection = chromadb_client.get_or_create_collection(
    "documents", metadata={"heuristic": "cosine"},
    )


class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5

class AnswerResponse(BaseModel):
    answer: str
    chunks_used: int


def split_text( text: str, chunk_size: int = 500, overlap: int = 50):
    
    chunks = []
    start = 0
    while start < len(text):
        end =  start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap

    return chunks

def embed_text(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model = "text-embedding-3-small",
        input = text,
    )
    return response.data[0].embedding


@app.post("/ingest")
async def ingest_document( file: UploadFile = File(...)):
    content = await file.read()
    
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a UTF-8 encoded text file.")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="File is empty.")

    chunks = split_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No valid text chunks found in the file.")
    
    ids = []
    embeddings = []
    documents = []

    for i, chunk in enumerate(chunks):
        chunks_id = f"{file.filename}_chunk_{i}"
        embedding = embed_text(chunk)
        ids.append(chunks_id)
        embeddings.append(embedding)
        documents.append(chunk)
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
    )

    return { "filename" : file.filename, "chunks_added": len(chunks), "message": f"Ingested {len(chunks)} chunks into vector DB", }

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):

    query_vector = embed_text(request.question)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=request.top_k,
    )

    # results["documents"] is a list of lists — [[chunk1, chunk2, chunk3]]
    # [0] gets the inner list for our single query
    chunks = results["documents"][0]

    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant documents found for the question.")
    
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""You are a helpful assistant. Answer the question using ONLY 
    the context provided below. If the answer is not in the context, 
    say "I don't have enough information to answer that."

    Context:
    {context}

    Question: {request.question}

    Answer:"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
        )
    
    answer = response.choices[0].message.content

    return AnswerResponse(answer=answer, chunks_used=len(chunks))

@app.get("/")
def root():
    doc_count = collection.count()
    return {
        "status":       "running",
        "chunks_stored": doc_count,
        "message":      "POST /ingest a .txt file, then POST /ask a question",
    }





