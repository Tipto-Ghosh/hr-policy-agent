from __future__ import annotations
import hashlib
from pathlib import Path
from langchain_core.documents import Document


def compute_source_doc_id(file_path: Path) -> str:
    """
    Stable ID for a source file. 
    """
    digest = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()[:12]
    return f"{Path(file_path).stem}-{digest}"


def attach_source_doc_id(chunks: list[Document], source_doc_id: str) -> list[Document]:
    """
    Attach source_doc_id to each chunk.
    """
    for chunk in chunks:
        chunk.metadata["source_doc_id"] = source_doc_id
    return chunks