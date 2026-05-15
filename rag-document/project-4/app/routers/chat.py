from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
from ..ingestion import ensure_collection, ingest_file, delete_document, list_documents
from ..graph import rag_graph




router = APIRouter(prefix="", tags=["chat"])

class QuestionRequest(BaseModel):
    question: str
    session_id: str = 'default'

class Source(BaseModel):
    filename: str
    page: int|str
    excerpt: str

class AnswerResponse(BaseModel):
    answer: str
    sources: list[Source]
    query_type: str
    rewrite_count: int
    answer_grade: str


session_store: dict[str, list] = {}


@router.post('/ingest', status_code=201)
async def ingest_document(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {'.pdf', '.txt'}:
        raise HTTPException(status_code=415, detail= f'Please use extension .pdf or .txt, not {suffix}')
    save_path = Path('uploads')/file.filename
    save_path.write_bytes(await file.read())

    try:
        result = ingest_file(str(save_path), file.filename)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    return result

@router.post('/ask', response_model = AnswerResponse)
async def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail='Question cannot be empty')
    
    history = session_store.get(request.session_id, [])

    initial_state = {
        "question":          request.question,
        "original_question": request.question,
        "query_type":        "",
        "documents":         [],
        "doc_grade":         "",
        "rewrite_count":     0,
        "generation":        "",
        "answer_grade":      "",
        "chat_history":      history,
    }

    try:
        final_state = rag_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    session_store[request.session_id] = final_state.get('chat_history', [])

    sources = []
    seen = set()

    for doc in final_state.get('documents', []):
        fname = doc.metadata.get("filename", "unknown")
        page  = doc.metadata.get("page", "?")
        key   = f"{fname}:p{page}"

        if key not in seen:
            seen.add(key)
            sources.append(Source(
                filename=fname,
                page=page,
                excerpt=doc.page_content[:150] + "...",
            ))

    return AnswerResponse(
        answer=final_state.get("generation", ""),
        sources=sources,
        query_type=final_state.get("query_type", "rag"),
        rewrite_count=final_state.get("rewrite_count", 0),
        answer_grade=final_state.get("answer_grade", ""),
    )

@router.get('/documents')
def get_documents():
    return {'document': list_documents()}


@router.delete('/document/{filename}', status_code=204)
def remove_document(filename: str):
    count = delete_document(filename)
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{filename}' not found"
        )
    
@router.delete("/sessions/{session_id}", status_code=204)
def clear_session(session_id: str):
    """Clear conversation memory for a session."""
    session_store.pop(session_id, None)


