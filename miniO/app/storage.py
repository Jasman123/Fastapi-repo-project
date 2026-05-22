import io
import asyncio
from datetime import timedelta
from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from app.config import get_settings


@lru_cache()
def _client() -> Minio:
    cfg = get_settings()
    return Minio(
        endpoint= cfg.minio_endpoint,
        access_key= cfg.minio_access_key,
        secret_key= cfg.minio_secret_key,
        secure= cfg.minio_secure,
    )

async def ensure_bucket() -> None:
    cfg = get_settings()
    c = _client()

    exists = await asyncio.to_thread(c.bucket_exists, cfg.minio_bucket)
    if not exists:
        await asyncio.to_thread(c.make_bucket, cfg.minio_bucket)

async def upload(key: str, data: bytes, content_type: str) -> None:
    cfg = get_settings()

    def _run():
        _client.put_object(
            bucket_name = cfg.minio_bucket,
            object_name = key,
            data = io.BytesIO(data),
            length = len(data),
            content_type = content_type,
        )
    await asyncio. to_thread(_run)


async def download(key: str) -> bytes:
    cfg = get_settings()
    def _run():
        resp = None
        try:
            resp = _client().get_object(cfg.minio_bucket, key)
            return resp.read()
        
        finally:
            if resp:
                resp.close()
                resp.release_conn()

    return await asyncio.to_thread(_run)

async def remove(key: str) -> None:
    cfg = get_settings()
    await asyncio.to_thread(
        _client().remove_bucket, cfg.minio_bucket, key
    )

async def presign(key: str) -> str:
    cfg = get_settings()
    url = await asyncio.to_thread(   
        _client().presigned_get_object,
        cfg.minio_bucket,
        key,
        timedelta(minutes=cfg.presign_expiry_minutes)
    )

    return url