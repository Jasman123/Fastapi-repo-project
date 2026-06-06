import logging 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.chroma_db import add_document, search
from app.config import get_settings


logger = logging.getLogger(__name__)

def ingest_document(doc_id: str, title: str, content: str) -> dict:
    logger.info(f"ingesting: doc_id={doc_id}, chars={len(content)}")
    chunk_count = add_document(doc_id=doc_id, title=title, content=content)
    logger.info(f"Done: {chunk_count} chunks stored for {doc_id}")
    return {
        "doc_id": doc_id,
        "title": title,
        "chunk_stored": chunk_count,
        "status": "success",
    }

def answer_question(question: str, top_k: int = 3) -> dict:
    settings = get_settings()
    logger.info(f"Answering: {question[:60]}...")
    results = search(query=question, k=top_k)

    if not results:
        return {
            "question": question,
            "answer":"Tidak ada dokumen yang tersimpan",
            "source" : [],
        }
    
    sources = []
    context_parts = []

    for i, (doc, score) in enumerate(results):
        sources.append({
            "doc_id": doc.metadata.get("doc_id", ""),
            "title": doc.metadata.get("title", ""),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "similarity": round(1 - score, 4),
            "text_preview": doc.page_content[:150] + "...",
        })
        context_parts.append(
            f"[Sumber {i+1}: {doc.metadata.get('title', '')}]\n"
            f"{doc.page_content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    llm = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o-mini", temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Jawab pertanyaan berdasarkan context yang diberikan. "
         "Jika tidak ada informasi di context, katakan tidak tahu. "
         "Gunakan Bahasa Indonesia."),
        ("user",
         "Context:\n{context}\n\n"
         "Pertanyaan: {question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question})

    return {"question": question, "answer": answer, "sources": sources}

