import io
import asyncio
from datetime import timedelta
from minio import Minio
from minio.error import S3Error


class MiniOStorage:

    def __init__(self, client: Minio, bucket: str, expiry_minutes: int):
        self._client = client
        self._bucket = bucket
        self._expiry = expiry_minutes

    
    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        def _run():
            self._client.put_object(
                bucket_name = self._bucket,
                object_name = key, 
                data = io.BytesIO(data),
                length = len(data),
                content_type = content_type,
            )
        await asyncio.to_thread(_run)
    
    async def download(self, key: str) -> bytes:
        def _run():
            resp = None
            try:
                resp = self._client.get_object(self._bucket, key)
                return resp.read()
            finally:
                if resp:
                    resp.close()
                    resp.release_conn()

        return await asyncio.to_thread(_run)
    
    async def remove(self, key: str) -> None:
        await asyncio.to_thread(
            self._client.remove_object, self._bucket, key
        )

    async def presign(self, key: str) -> str:
        return await asyncio.to_thread(
            self._client.presigned_get_object,
            self._bucket,
            key,
            timedelta(minutes=self._expiry)
        )
    
    async def ensure_bucket(self) -> None:
        exists = await asyncio.to_thread(
            self._client.bucket_exists, self._bucket
        )

        if not exists:
            await asyncio.to_thread(self._client.make_bucket, self._bucket)


