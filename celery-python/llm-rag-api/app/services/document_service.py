import logging
from app.db.chroma import VectorStoreRepository
from app.utils.text_splitter import split_text_into_chunks, build_langchain_documents
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class DocumentService:

    def __init__(self):
        self._repo = VectorStoreRepository()
        self._settings = get_settings()

    def ingest_text(self, doc_id: str, title: str, content: str) -> dict:
        logger.info(f"Ingesting text: doc_id={doc_id}, chars={len(content)}")

        chunks = split_text_into_chunks(
            text = content,
            chunk_size = self._settings.chunk_size,
            chunk_overlap = self._settings.chunk_overlap,
        )

        if not chunks:
            return {
                "doc_id": doc_id,
                "status" : "skipped",
                "reason": "No_chunks_generated",
            }
        
        documents, ids = build_langchain_documents(
            chunks = chunks,
            doc_id = doc_id,
            title = title,
            extra_metadata = {"source_type": "text"},
        )

        self._repo.delete_by_doc_id(doc_id)
        self._repo.add_documents(documents = documents, ids = ids)

        logger.info(f"Ingested {len(chunks)} chunks for doc_id={doc_id}")
        return {
            "doc_id": doc_id,
            "title": title,
            "status":"success",
            "chunks_stored": len(chunks),
        }

    def ingest_from_parsed_pdf(self, doc_id: str, title: str, pdf_data: dict) -> dict:
        content = pdf_data.get("content","")
        pdf_metadata = pdf_data.get("metadata", {})
        

        
        logger.info(
            f"Ingesting PDF: doc_id={doc_id}, "
            f"pages={pdf_metadata['total_pages']}, "
            f"chars={pdf_metadata['total_chars']}"
        )

        chunks = split_text_into_chunks(
            text = content,
            chunk_size = self._settings.chunk_size,
            chunk_overlap = self._settings.chunk_overlap,
        )

        if not chunks:
            return{
                "doc_id": doc_id,
                "status": "skipped",
                "reason": "No_chunks_generated",
            }
        documents, ids = build_langchain_documents(
            chunks = chunks,
            doc_id = doc_id,
            title = title,
            extra_metadata = {
                "source_type": "pdf",
                "source_filename" :pdf_metadata.get("file_name", ""),
                "total_pages": pdf_metadata.get("total_pages", 0),
            }
        )
        self._repo.delete_by_doc_id(doc_id)
        self._repo.add_documents(documents = documents, ids = ids)


        logger.info(f"Ingested {len(chunks)} chunks from PDF doc_id={doc_id}")
        return {
            "doc_id": doc_id,
            "title": title,
            "status": "success",
            "chunks_stored": len(chunks),
            "pdf_metadata": pdf_metadata,
        }

    def delete_document(self, doc_id: str) -> dict:
        chunks_removed = self._repo.delete_by_doc_id(doc_id)
        deleted = chunks_removed > 0

        return {
            "doc_id": doc_id,
            "deleted": deleted,
            "chunks_removed": chunks_removed,
        }

    def list_documents(self) -> list[dict]:
        return self._repo.list_documents()
        



