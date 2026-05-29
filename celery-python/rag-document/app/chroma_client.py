import chromadb
from chromadb.config import Settings as ChromaSettings
from functools import lru_cache
from app.config import get_settings


@lru_cache
def get_chroma_client() -> chromadb.PersistentClient:
    settings = get_settings()
    return chromadb.PersistentClient(
        path = settings.chroma_persits_dir, settings = ChromaSettings(anonymized_telemetry=False),
    )

def get_collection():
    settings = get_settings()
    client = get_chroma_client()

    return client.get_or_create_collection(
        name = settings.chroma_collection_name, embedding_function = None, metadata={"hnsw:space": "cosine"},
    )