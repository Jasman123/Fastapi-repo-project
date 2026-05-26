from typing import Optional 
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel


from app.dependencies import get_service
from app.service import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


class CreateNoteRequest(BaseModel):
    title: str
    body: str


class UpdateNoteRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None

@router.post("/", status_code=201)
async def create_note(payload: CreateNoteRequest, svc: NoteService = Depends(get_service),):
    return await svc.create(title = payload.title, body= payload.body)

@router.get("/")
async def list_notes(svc: NoteService = Depends(get_service)):
    notes = await svc.list_all()
    return {"notes": notes, "total":len(notes)}

@router.get("/{note_id}")
async def get_note(note_id: str, svc: NoteService = Depends(get_service)):
    try:
        return await svc.get(note_id)
    except ValueError:
        raise HTTPException(404, f"note {note_id} not found")
    

@router.put("/{note_id}")
async def update_note( note_id: str, payload: UpdateNoteRequest, svc: NoteService = Depends(get_service)):
    try:
        return await svc.update(note_id, title=payload.title, body=payload.body)
    except ValueError as e:
        raise HTTPException(404, str(e))
    

@router.delete("/{note_id}", status_code=204)
async def delete_note( note_id: str, svc: NoteService = Depends(get_service)):
    try:
        await svc.delete(note_id)

    except ValueError:
        raise HTTPException(404, f"note {note_id} not found")
    

@router.post("/{note_id}/attach", status_code=200)
async def attach_file( note_id: str, file: UploadFile, svc: NoteService = Depends(get_service)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    
    try:
        return await svc.attach_file(
            note_id = note_id,
            filename = file.filename or "attachment",
            data = data,
            content_type= file.content_type or "application/octet-stream",
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    

@router.get("/{note_id}/attachment/url")
async def get_attachment_url(note_id: str, svc: NoteService = Depends(get_service)):
    try:
        url = await svc.get_attachment_url(note_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"note_id": note_id, "url":url}


@router.get("/{note_id}/attachment/file")
async def donwload_attachement(note_id: str, svc: NoteService = Depends(get_service)):
    try:
        blob, content_type, filename = await svc.download_attachment(note_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    
    return Response(content=blob, media_type=content_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})