import tempfile
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException


from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from .config import settings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
    add_start_index=True
)


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=settings.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR
    )

async def ingest_file(file: UploadFile):
    suffix = Path(file.filename).suffix.lower()

    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(
            status_code = 415,
            detail = f'Unsupported file type {suffix}. Use .pdf or .txt'
        )
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            loader = PyMuPDFLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path)

        raw_docs = loader.load()

        if not raw_docs:
            raise HTTPException(
                status_code = 400,
                detail = "No text found in the uploaded file."
            )
        
        for doc in raw_docs:
           doc.metadata["source"] = file.filename
        
        chunks = splitter.split_documents(raw_docs)
        if not chunks:
            raise HTTPException(
                status_code = 400,
                detail = "Failed to split the document into chunks."
            )
        
        vectorstore = get_vectorstore()
        vectorstore.add_documents(chunks)
        
        return{
            "filename": file.filename,
            "pages" : len(raw_docs),
            "chunks": len(chunks),
            "message": f'Successfully ingested {file.filename} with {len(chunks)} chunks.'
        }
    
    finally:
        os.remove(tmp_path)


