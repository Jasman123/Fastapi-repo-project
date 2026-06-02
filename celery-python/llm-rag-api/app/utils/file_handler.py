import uuid
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def save_upload(content: bytes, filename: str, upload_dir: str) -> Path:
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    safe_name = filename.replace(" ", "_")
    unique_prefix = uuid.uuid4().hex[:8]
    file_path = upload_path / f"{unique_prefix}_{safe_name}"

    file_path.write_bytes(content)
    logger.info(f"File saved: {file_path} ({len(content)} bytes)")
    return file_path

def delete_file(file_path: str) -> bool:

    path = Path(file_path)
    if path.exists():
        path.unlink()
        logger.info(f"file deleted: {file_path}")
        return True
    
    return False

def validate_file_size(content: bytes, max_bytes: int) -> None:
    if len(content) > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise ValueError(f"File size exceeds the maximum allowed size of {max_mb:.2f} MB")
    
def validate_pdf_extension(filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Unsupported file type. Only PDF files are allowed.")

