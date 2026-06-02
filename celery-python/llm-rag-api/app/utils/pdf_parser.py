import logging
from pathlib import Path
from pypdf import PdfReader

logger =  logging.getLogger(__name__)

def parse_pdf(file_path: str) -> str:

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Unsupported file type: {path.suffix}. Only PDF files are supported.")
    
    logger.info(f"Parsing PDF file: {file_path}")

    reader = PdfReader(file_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append({
                "page_number": i + 1,
                "text": text,
                "char_count": len(text),
            })
    full_text = "\n\n".join(page["text"] for page in pages)
    metadata = {
        "file_name": path.name,
        "file_size_bytes": path.stat().st_size,
        "total_pages": len(reader.pages),
        "pages_with_content": len(pages),
        "total_chars": len(full_text),
    }
    
    if reader.metadata:
        for attr, key in [("title", "pdf_title"), ("author", "pdf_author")]:
            value = getattr(reader.metadata, attr, None)
            if value:
                metadata[key] = value
    
    logger.info(f"PDF parsed: {metadata['total_pages']} pages, {metadata['total_chars']} chars extracted")

    return {
        "content": full_text,
        "metadata": metadata,
        "pages": pages,
    }