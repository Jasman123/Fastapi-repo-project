from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..ingestion import ensure_collection, ingest_file
from fastapi import UploadFile, File
from pathlib import Path
from ..graph import rag_graph

router = APIRouter(prefix="", tags=["chat"])

class QuestionRequest(BaseModel):
    question: str
    session_id: str = "default"
    stream: bool = False

class AnswerResponse(BaseModel):
    answer: str
    sources: list[dict]
    web_search: bool


session_store: dict[str,list] = {}


@router.post("/ingest", status_code=201)
async def ingest_document(file: UploadFile = File(...)):
    allowed = {".pdf", ".txt"}
    suffix = Path(file.filename).suffix.lower()

    if suffix not in allowed:
        raise HTTPException(status_code=415, detail=f"Use PDF or TXT, not {suffix}")
    
    save_path = Path("uploads")/file.filename
    save_path.write_bytes(await file.read())

    try:
        result = await ingest_file(str(save_path), file.filename)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    return result

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    history = session_store.get(request.session_id, [])

    initial_state = {
        "question": request.question,
        "documents": [],
        "generation": "",
        "chat_history": history,
        "web_search": False,
        "doc_grade": "",
    }

    try:
        final_state = rag_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    session_store[request.session_id] = final_state.get("chat_history", [])

    sources = []
    seen = set()
    for doc in final_state.get("documents", []):
        fname = doc.metadata.get('filename', 'unknown')
        page =  doc.metadata.get('page', '?')
        key = f'{fname}: p{page}'

        if key not in seen :
            seen.add(key)
            sources.append({
                'filename': fname,
                'page': page,
                'excerpt': doc.page_content[:150] + "..."
            })

    return AnswerResponse(
        answer = final_state.get("generation", ""),
        sources = sources,
        web_search= final_state.get("web_search", False),
    )

@router.delete("/sessions/{session_id}", status_code=204)
def clear_session(session_id: str):
    session_store.pop(session_id, None)

    

    
    

