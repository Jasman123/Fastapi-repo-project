from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap,
        length_function = len,
        separators = ["\n\n", "\n", " ", "", ". "]
    )
    return splitter.split_text(text)

def build_langchain_documents(chunks: list[str], doc_id: str, title: str, extra_metadata: dict|None = None,) -> tuple[list[Document], list[str]]:
    base_metadata = {
        "doc_id": doc_id,
        "title": title,
        "total_chunks" : len(chunks),
        **(extra_metadata or {}),
    }

    documents = [
        Document(
            page_content = chunk,
            metadata = {
                **base_metadata,
                "chunk_index": i,
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    ids = [f"{doc_id}::chunk_{i}" for i in range(len(chunks))]
    return documents, ids