from functools import lru_cache
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import get_settings


@lru_cache
def get_store()-> Chroma:
    settings = get_settings()
    embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key, model=settings.model_embedding)
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir,
    )

def add_document(doc_id: str, title: str, content:str) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50,)
    chunks = splitter.split_text(content)
    if not chunks:
        return 0
    
    documents = [
        Document(
            page_content=chunk, metadata={
                "doc_id": doc_id,
                "title": title,
                "chunk_index": i,
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    ids = [f"{doc_id}:: chunks_{i}" for i in range(len(chunks))]
    store = get_store()

    try:
        store.delete(where={"doc_id": doc_id})
    except Exception:
        pass

    store.add_documents(documents=documents, ids=ids)
    
    return len(chunks)

def search(query: str, k: int=3) -> list[tuple]:
    store = get_store()
    return store.similarity_search_with_score(query=query, k=k)

def delete_document(doc_id: str) -> None:
    store = get_store()
    try:
        store.delete(where={"doc_id": doc_id})
    except Exception:
        pass