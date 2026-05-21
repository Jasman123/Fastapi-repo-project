import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentRecord(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    bucket: str
    uploaded_at: datetime


class UploadResponse(BaseModel):
    id: str
    filename: str
    size_bytes: int
    storage_key: str
    download_url: str

class DocumentList
