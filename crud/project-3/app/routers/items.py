from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .. import crud 
from ..schemas import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse

router = APIRouter( prefix="/items", tags=["items"])


@router.post("/", response_model = ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item_in: ItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_item(db, item_in)

@router.get("/", response_model=ItemListResponse)
async def list_items(db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1), size: int = Query(100, ge=1, le=100)):
    skip = (page-1) * size
    items, total = await crud.get_items(db, skip=skip, limit=size)
    return ItemListResponse(items=items, total=total, page=page, size=size)

@router.get("/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item_in: ItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await crud.update_item(db, item_id, item_in)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    delete = await crud.delete_item(db, item_id)
    if not delete:
        raise HTTPException(status_code=404, detail="Item not found")
    return None
