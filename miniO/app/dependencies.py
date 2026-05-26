from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from minio import Minio


from app.config import get_settings
from app.database import get_db
from app.storage import MiniOStorage


@lru_cache()
def _minio_client() -> Minio:
    cfg = get_settings()
    return Minio(
        endpoint = cfg.minio_endpoint,
        access_key = cfg.minio_access_key,
        secret_key = cfg.minio_secret_key,
        secure = cfg.minio_secure,
    )


def get_storage() -> MiniOStorage:
    cfg = get_settings()
    return MiniOStorage(
        client = _minio_client(),
        bucket = cfg.minio_bucket,
        expiry_minutes = cfg.presign_expiry_minutes,
    )

def get_service( session: AsyncSession = Depends(get_db), storage: MiniOStorage = Depends(get_storage)) -> "NoteService":
    from app.service import NoteService
    return NoteService(storage=storage, session = session)