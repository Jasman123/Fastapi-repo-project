from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .models import Item
from .schemas import ItemCreate, ItemUpdate


async def create_item(db: AsyncSession, item_in: ItemCreate) -> Item:
    item = Item(**item_in.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item

async def get_item(db: AsyncSession, item_id: int) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalars().first()

async def get_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item))
    return result.scalars().all()

async def update_item(db: AsyncSession, item_id: int, item_in: ItemUpdate) -> Item|None:
    item = await get_item(db, item_id)
    if not item:
        return None
    
    for key, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    item.updated_at = datetime.now(timezone.utc)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item

async def delete_item(db: AsyncSession, item_id: int) -> bool:
    item = await get_item(db, item_id)
    if not item:
        return False
    
    await db.delete(item)
    return True
