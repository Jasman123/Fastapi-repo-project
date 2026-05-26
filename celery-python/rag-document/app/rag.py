# app/rag.py
"""
RAG query logic — retrieval + generation.

Flow:
1. Embed user question
2. Query ChromaDB untuk top-K similar chunks
3. Bangun prompt dengan context
4. Generate answer via OpenAI chat
"""
import structlog
from app.openai_client import generate_embedding, chat_completion
from app.chroma_client import get_collection
from app.config import get_settings
from app.models import SourceChunk, QueryResponse

logger = structlog.get_logger()


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

Rules:
- Only use information from the provided context to answer
- If the context doesn't contain the answer, say "I don't have enough information to answer that"
- Be concise and accurate
- Cite which document(s) you used (mention doc_id)"""


def _build_context_prompt(question: str, chunks: list[dict]) -> list[dict]:
    """
    Bangun messages untuk OpenAI chat completion.
    
    Format: [system, user] dengan context disisipkan di user message.
    """
    # Format context: setiap chunk dengan metadata sumbernya
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {i}] (doc_id: {chunk['doc_id']}, chunk {chunk['chunk_index']})\n"
            f"{chunk['text']}"
        )
    context = "\n\n".join(context_parts)
    
    user_message = f"""Context:
{context}

---

Question: {question}

Answer based on the context above."""
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def query_rag(question: str, top_k: int = 3) -> QueryResponse:
    """
    Main RAG query function.
    
    Sync (bukan Celery task) karena:
    - User expect immediate response (<3 detik)
    - Tidak ada parallelization benefit
    - Simpler error handling
    """
    settings = get_settings()
    log = logger.bind(question=question[:100], top_k=top_k)
    log.info("rag.query.started")
    
    # === Step 1: Embed question ===
    question_embedding = generate_embedding(question)
    log.info("rag.query.embedded")
    
    # === Step 2: Query ChromaDB ===
    collection = get_collection()
    
    # query_embeddings = list of vectors (kalau mau batch query)
    # n_results = top-k
    # include = field apa yang mau di-return
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    
    # Results format ChromaDB:
    # {
    #   "ids": [["id1", "id2", ...]],          ← nested list karena batch query
    #   "documents": [["text1", "text2", ...]],
    #   "metadatas": [[{...}, {...}, ...]],
    #   "distances": [[0.1, 0.2, ...]]
    # }
    # [0] karena kita query 1 question
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    
    if not documents:
        log.warning("rag.query.no_results")
        return QueryResponse(
            question=question,
            answer="I don't have any documents indexed yet. Please ingest some documents first.",
            sources=[],
            model=settings.chat_model,
        )
    
    # Build source chunks untuk response
    # Note: ChromaDB distance untuk cosine = 1 - similarity
    # Jadi similarity = 1 - distance
    source_chunks = [
        SourceChunk(
            doc_id=meta["doc_id"],
            chunk_index=meta["chunk_index"],
            text=doc,
            similarity_score=round(1 - dist, 4),
        )
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]
    
    log.info(
        "rag.query.retrieved",
        chunks_found=len(source_chunks),
        top_score=source_chunks[0].similarity_score if source_chunks else None,
    )
    
    # === Step 3: Build prompt & generate ===
    chunks_for_prompt = [
        {
            "doc_id": chunk.doc_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
        }
        for chunk in source_chunks
    ]
    messages = _build_context_prompt(question, chunks_for_prompt)
    
    answer = chat_completion(messages, temperature=0.3)
    log.info("rag.query.completed", answer_length=len(answer))
    
    return QueryResponse(
        question=question,
        answer=answer,
        sources=source_chunks,
        model=settings.chat_model,
    )