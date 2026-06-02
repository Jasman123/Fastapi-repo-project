from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from app.api.deps import get_document_service
from app.core.config import get_settings
from app.models.schemas import (
    TextIngestRequest,
    TaskSubmittedResponse,
    PDFUploadResponse,
    DeleteResponse,
    DocumentInfo,
)
from app.services.document_service import DocumentService
from app.tasks.document_task import ingest_text_task, ingest_pdf_task
from app.utils.file_handler import (
    delete_file,
    save_upload,
    validate_file_size,
    validate_pdf_extension,
)

router  = APIRouter()

@router.post("/ingest", response_model = TaskSubmittedResponse, status_code = 202)
async def ingest_text( payload: TextIngestRequest,) :
    try:
        task = ingest_text_task.delay(
            doc_id = payload.doc_id,
            title = payload.title,
            content = payload.content,
        )
        return TaskSubmittedResponse(task_id = task.id, status = "queued")
    except Exception as exc:
        raise HTTPException(status_code = 503, detail = "Task queue unavailabe")
    
@router.post("/upload-pdf", response_model = PDFUploadResponse, status_code = 202)
async def upload_pdf( file: UploadFile = File(...), doc_id: str = Form(...), title: str = Form(None),):
    settings = get_settings()
    try:
        validate_pdf_extension(file.filename)
        content = await file.read()
        validate_file_size(content, settings.max_file_size_bytes)
    except ValueError as exc:
        raise HTTPException(status_code = 400, detail = str(exc))
    
    try:
        saved_path = save_upload(
            content = content,
            filename = file.filename,
            upload_dir = settings.upload_dir,
        )
    except Exception as exc:
        raise HTTPException(status_code = 500, detail = f"Failed to save file: {exc}")
    
    try:
        task = ingest_pdf_task.delay(
            file_path = str(saved_path),
            doc_id = doc_id,
            title = title,
        )
        return PDFUploadResponse(
            task_id = task.id,
            doc_id = doc_id,
            filename = file.filename,
            file_size_bytes = len(content),
            status = "queued",  
        )
    except Exception as exc:
        delete_file(str(saved_path))
        raise HTTPException(status_code = 503, detail = "Task queue unavalailabe")
    

@router.get("", response_model = list[DocumentInfo])
async def list_documents( service: DocumentService = Depends(get_document_service),):
    docs = service.list_documents()
    return [DocumentInfo(**d) for d in docs]


@router.delete("/{doc_id}", response_model = DeleteResponse)
async def delete_document( doc_id: str, service: DocumentService = Depends(get_document_service),):
    result = service.delete_document(doc_id)
    return DeleteResponse(**result)

