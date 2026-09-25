# metadata.py
from __future__ import annotations
import hashlib
from pathlib import Path
from langchain_core.documents import Document


def compute_source_doc_id(file_path: Path) -> str:
    digest = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()[:12]
    return f"{Path(file_path).stem}-{digest}"


def attach_source_doc_id(chunks: list[Document], source_doc_id: str) -> list[Document]:
    for chunk in chunks:
        chunk.metadata["source_doc_id"] = source_doc_id
    return chunks


def build_breadcrumb(meta: dict) -> str:
    parts = [
        meta.get("Section", ""),
        meta.get("SubSection", ""),
        meta.get("SubSubSection", ""),
        meta.get("SubSubSubSection", ""),
    ]
    return " > ".join(p for p in parts if p)


def enrich_chunks(
    chunks: list[Document],
    source_doc_id: str,
    extra_metadata: dict | None = None,
) -> list[Document]:
    extra_metadata = extra_metadata or {}
    enriched = []
    for chunk in chunks:
        enriched.append(Document(
            page_content=chunk.page_content,
            metadata={
                **chunk.metadata,
                **extra_metadata,
                "source_doc_id": source_doc_id,
                "breadcrumb": build_breadcrumb(chunk.metadata),
            },
        ))
    return enriched