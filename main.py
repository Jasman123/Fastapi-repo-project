from fastapi import FastAPI,Query
from typing import Optional

app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

# Query params: /items?skip=0&limit=10&q=laptop

@app.get("/items")
async def list_items(skip: int = 0, limit: int = Query(default=10, lte=100), q: Optional[str] = None):
    return {"skip": skip, "limit": limit, "q": q}