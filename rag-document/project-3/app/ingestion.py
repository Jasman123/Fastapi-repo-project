from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from .nodes import embeddings
from .config import settings

qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def ensure_collection() -> None:

    existing = [c.name for c in qdrant_client.get_collections().collections]

    if settings.QDRANT_COLLECTION not in existing:
        qdrant_client.create_collection(
            collection_name = settings.QDRANT_COLLECTION,
            vectors_config = VectorParams(
                size = settings.QDRANT_VECTOR_SIZE,
                distance = Distance.COSINE,
            ),
        )
        print(f"Created Qdrant collection : {settings.QDRANT_COLLECTION}")


async def ingest_file(file_path: str, filename: str) -> dict:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyMuPDFLoader(str(path))
    elif suffix == ".txt":
        loader = TextLoader(str(path), encoding='utf-8')
    else:
        raise ValueError(f'Unsupported: {suffix}')
    

    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = settings.CHUNK_SIZE,
        chunk_overlap = settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for chunk in chunks:
        chunk.metadata["filename"] = filename

    vectorstore = QdrantVectorStore(
        client = qdrant_client,
        collection_name = settings.QDRANT_COLLECTION,
        embeddings = embeddings,
    )

    ids = vectorstore.add_documents(chunks)

    return {
        "filename": filename,
        "pages": len(documents),
        "chunks": len(chunks),
        "ids": len(ids),
    }