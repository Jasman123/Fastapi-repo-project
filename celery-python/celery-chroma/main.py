import os
from fastapi import FastAPI
from app.routers import router
from app.config import get_settings


settings = get_settings()

os.makedirs(settings.chroma_dir, exist_ok=True)

app = FastAPI(
    title="AI Task API", description="Celery + Langchain + ChromaDB", version="1.0.0",
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}