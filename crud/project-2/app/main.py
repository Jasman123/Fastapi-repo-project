from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, Base, get_db
from .schemas import ItemCreate, ItemUpdate, ItemResponse
from . import crud


@asynccontextmanager
async def lifespan(app : FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    title="Async CRUD API with FastAPI and SQLAlchemy",
)

@app.post("/items/", response_model=ItemResponse, status_code=201)
async def create_item(item_in: ItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_item(db, item_in)

@app.get("/items", response_model=list[ItemResponse])
async def list_items(db: AsyncSession = Depends(get_db)):
    return await crud.get_items(db)

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item_in: ItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await crud.update_item(db, item_id, item_in)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    delete = await crud.delete_item(db, item_id)
    if not delete:
        raise HTTPException(status_code=404, detail="Item not found")
    return None