from functools import lru_cache
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings

@lru_cache
def get_embeddings_function():
    settings = get_settings()
    return OpenAIEmbeddings(
        model = settings.embedding_model,
        openai_api_key = settings.openai_api_key,
    )

@lru_cache
def get_vectorstore() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name = settings.chroma_collection_name,
        embedding_function = get_embeddings_function(),
        persist_directory = settings.chroma_persits_dir,
    )

class VectorStoreRepository:

    def __init__(self):
        self._store = get_vectorstore()

    def add_documents(self, documents: list, ids: list[str]) -> None:
        self._store.add_documents(documents = documents, ids = ids)
    
    def similarity_search(self, query: str, k: int = 3) -> list[dict]:
        return self._store.similarity_search_with_score(query = query, k=k)
    
    def delete_by_doc_id(self, doc_id: str) -> None:
        existing = self._store.get(where = {"doc_id": doc_id})
        count = len(existing.get("ids", [] ))

        if count > 0:
            self._store.delete(where = {"doc_id": doc_id})

        return count
    
    def get_by_doc_id(self, doc_id: str) -> dict:
        return self._store.get(where = {"doc_id": doc_id})
    
    def list_documents(self) -> list[dict]:
        all_items = self._store.get()

        if not all_items["ids"]:
            return []
        
        doc_map : dict[str, dict] = {}

        for metadata in all_items["metadatas"]:
            doc_id = metadata.get("doc_id", "unknown")
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "doc_id": doc_id,
                    "title": metadata.get("title", "untitled"),
                    "source_type": metadata.get("source_type", "text"),
                    "chunks_count": 0,
                }
            doc_map[doc_id]["chunks_count"] += 1


        return list(doc_map.values())