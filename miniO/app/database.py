from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)

from sqlalchemy import select, delete, update
from app.config import get_settings
from app.models import Note


cfg = get_settings()

engine = create_async_engine(cfg.postgres_dsn, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def db_create(session: AsyncSession, note: dict) -> dict:
    obj = Note(
        id=note["id"], title=note["title"], body=note["body"],
        attachment_key=note.get("attachment_key", ""),
        attachment_name=note.get("attachment_name", "noname"),
    )

    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj.to_dict()


async def db_get(session: AsyncSession, note_id: str) -> Optional[dict]:
    result = await session.execute(select(Note).where(Note.id == note_id))
    row = result.scalar_one_or_none()
    return row.to_dict() if row else None


async def db_list(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Note).order_by(Note.created_at.desc())
    )

    return [r.to_dict() for r in result.scalars().all()]

async def db_update(session: AsyncSession, note_id: str, fields: dict) -> Optional[dict]:
    result = await session.execute(update(Note).where(Note.id == note_id).values(**fields).returning(Note))

    await session.commit()
    row = result.scalar_one_or_none()
    return row.to_dict() if row else None


async def db_delete(session: AsyncSession, note_id: str) -> bool:
    result = await session.execute(delete(Note).where(Note.id == note_id))
    await session.commit()
    return result.rowcount == 1

async def db_set_attachment(session: AsyncSession, note_id: str, attachment_key: str, attachment_name: str) -> Optional[dict]:
    return await db_update(session, note_id, {
        "attachment_key": attachment_key,
        "attachment_name": attachment_name,
    },)
