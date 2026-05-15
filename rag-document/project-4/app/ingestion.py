from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus as _BaseMilvus
from langchain_openai import OpenAIEmbeddings
from pymilvus import connections, utility, Collection
from .config import settings


embeddings = OpenAIEmbeddings(
    model = "text-embedding-3-small", api_key = settings.OPENAI_API_KEY
)

MILVUS_CONNECTION = {
    "uri": settings.MILVUS_URI
}

# pymilvus 2.6.x MilvusClient uses ConnectionManager aliases ("cm-...") that are
# not registered in the ORM connections registry, so Collection(using=alias) fails.
# Override col to return None so langchain_milvus falls back to MilvusClient paths.
class Milvus(_BaseMilvus):
    @property
    def col(self):
        try:
            return super().col
        except Exception:
            return None

def get_vectorstore() -> Milvus:
    return Milvus(
        embedding_function = embeddings,
        collection_name = settings.MILVUS_COLLECTION,
        connection_args = MILVUS_CONNECTION,
        auto_id = True,
        drop_old = False,
        enable_dynamic_field = True,
    )

def ensure_collection() -> None:
    try:
        connections.connect(uri = settings.MILVUS_URI)
        print(f"Milvus connected. Collection '{settings.MILVUS_COLLECTION}' ready.")
    except Exception as e:
        raise RuntimeError(f"Cannot connect to Milvus at {settings.MILVUS_URI}: {e}")
    
def ingest_file(file_path: str, filename: str) -> dict:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyMuPDFLoader(str(path))
    elif suffix == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .pdf or .txt")
    
    documents = loader.load()
    if not documents:
        raise ValueError("Document is empty or could not be parsed")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = settings.CHUNK_SIZE,
        chunk_overlap = settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for chunk in chunks:
        chunk.metadata = {
            "filename": filename,
            "source": str(path),
            "page": chunk.metadata.get("page", 0),
        }

    vectorstore = get_vectorstore()
    ids = vectorstore.add_documents(chunks)

    return {
        "filename": filename,
        "pages": len(documents),
        "chunks": len(chunks),
        "ids": len(ids),
    }


def delete_document(filename: str) -> int:
    connections.connect(uri=settings.MILVUS_URI)
    col = Collection(settings.MILVUS_COLLECTION)
    col.load()

    expr = f'filename == "{filename}"'
    result = col.delete(expr)
    return result.delete_count

def list_documents() -> list[dict]:
    
    try:
        connections.connect(uri=settings.MILVUS_URI)
        col = Collection(settings.MILVUS_COLLECTION)
        col.load()

        results = col.query(
            expr = "filename != ''",
            output_field = ["filename"],
            limit = 16384,
        )

        counts: dict[str, int] ={}

        for r in results:
            fname = r.get("filename", "unknown")
            counts[fname] = counts.get(fname, 0) + 1

        return [{"filename": k, "chunks": v} for k, v in counts.items()]
    except Exception:
        return []

