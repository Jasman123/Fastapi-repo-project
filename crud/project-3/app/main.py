from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from .database import engine
from .config import settings
from .routers import items


@asynccontextmanager
async def lifespan(app : FastAPI):
    print("Creating database tables...")
    yield
    await engine.dispose()
    print("Shutting down application...")
     

app = FastAPI(
    lifespan=lifespan,
    title="Async CRUD API with FastAPI and SQLAlchemy",
)

app.include_router(items.router)

@app.get("/heatlh")
async def health():
    return {"status": "ok", "database": settings.DATABASE_URL}