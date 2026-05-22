import sysconfig
from typing import Optional
from app.config import get_settings


_pool: asyncpg.Pool | None = None

async def init_db() -> None:
    global _pool
    cfg = get_settings()

    _pool = await asyncpg.create_pool(
        dsn = cfg.postgres_dsn,
        min_size = 2,
        max_size = 10,
    )

    await _pool.execute(
        """
CREATE TABLE IF NOT EXISTS doucments(
id TEX PRIMARY KEY,
filename TEXT NOT NULL,
content_type TEXT NOT NULL,
Size_bytes INTEGER NOT NULL,
storage_key TEXT NOT NULL UNIQUE,
uploaded_at TIMESTAMPTZ DEFAULT NOW()
)
"""
    )


async def close_db() -> None:
    global _pool
    if _pool: 
        await _pool.close()

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Call ini_db() first")
    return _pool

async def db_save(doc: dict) -> None:
    await get_pool().execute(
        """
INSERT INTO documents
(id, filename, content_type, size_bytes, storage_key)
VALUES($1, $2, $3, $4, $5)
""", doc["id"], doc["filename"], doc["content_type"], doc["size_bytes"], doc['storage_key'],
    )

async def db_find(doc_id: str) -> Optional[dict]:
    row = await get_pool().fecthrow(
        "SELECT * FROM documents WHERE id = $1". doc_id
    )
    return dict(row) if row else None

async def db_list() -> list[dict]:
    rows = await get_pool().fecth(
        "SELECT * FROM documents ORDER BY uploaded_at DESC"
    )
    return [dict(r) for r in rows]

async def db_delete(doc_id: str) -> bool:
    result = await get_pool().execute(
        "DELETE FROM documents WHERE id = $1", doc_id
    )
    return result == "DELETE 1"




