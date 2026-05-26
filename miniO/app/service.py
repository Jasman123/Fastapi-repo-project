import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession


from app.storage import MiniOStorage
from app import database


class NoteService:

    def  __init__(self, storage: MiniOStorage, session: AsyncSession):
        self._storage = storage
        self._session = session
    
    async def create(self, title: str, body: str) -> dict:
        note = {
            "id" : str(uuid.uuid4()),
            "title" : title,
            "body" : body,
        }
        return await database.db_create(self._session, note)
    

    async def get(self, note_id: str) -> dict:
        note = await database.db_get(self._session, note_id)
        if note is None:
            raise ValueError(f"Note not found : {note_id}")
        return note
    

    async def list_all(self) -> list[dict]:
        return await database.db_list(self._session)
    
    async def update(self, note_id: str, title: Optional[str] = None, body: Optional[str] = None,) -> dict:
        fields = {}
        if title is not None:
            fields["title"] = title
        if body is not None:
            fields["body"] = body

        if not fields:
            raise ValueError("Nothing to update")
        
        note = await database.db_update(self._session, note_id, fields)
        if note is None:
            raise ValueError(f"Note not found {note_id}")
        return note
    
    async def delete(self, note_id: str) -> None:
        note = await database.db_get(self._session, note_id)
        if note is None :
            raise ValueError(f"Note not found: {note_id}")
        
        if note.get("attachment_key"):
            await self._storage.remove(note["attachment_key"])

        await database.db_delete(self._session, note_id)

    
    async def attach_file(self, note_id: str, filename: str, data: bytes, content_type: str,) -> dict:
        note = await database.db_get(self._session, note_id)
        if note is None:
            raise ValueError(f"note not found: {note_id}")
        
        if note.get("attachment_key"):
            await self._storage.remove(note["attachment_key"])

        attachment_key = f"attachment/{note_id}/{filename}"
        await self._storage.upload(attachment_key, data, content_type)

        return await database.db_set_attachment(
            self._session, note_id, attachment_key, filename
        )
    

    async def get_attachment_url(self, note_id: str) -> str:
        note = await database.db_get(self._session, note_id)
        if note is None:
            raise ValueError(f"note not found: {note_id}")
        if not note.get("attachment_key"):
            raise ValueError(f"Note {note_id} has no attachment")
        
        return await self._storage.presign(note["attachment_key"])
    

    async def download_attachment(self, note_id: str) -> tuple[bytes, str, str]:
        note = await database.db_get(self._session, note_id)
        if note is None:
            raise ValueError(f"note not found: {note_id}")
        if not note.get("attachment_key"):
            raise ValueError(f"note {note_id} has no attachment")
        
        blob = await self._storage.download(note["attachment_key"])
        return blob, "application/octet-stream", note["attachment_name"]





