# index.py
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

CHUNK_ID_SEPARATOR = "__"


def build_chunk_id(source_doc_id: str, chunk_content: str) -> str:
    """
    Deterministic ID from the chunk's CONTENT (not its position), so the
    same content always maps to the same vector, and changed content
    produces a new ID (old one is then deleted as "stale").
    """
    content_hash = hashlib.sha256(chunk_content.encode("utf-8")).hexdigest()[:16]
    return f"{source_doc_id}{CHUNK_ID_SEPARATOR}{content_hash}"


@dataclass
class ReindexReport:
    source_doc_id: str
    upserted_count: int
    upserted_ids: list[str] = field(default_factory=list)
    deleted_stale_ids: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"source_doc_id={self.source_doc_id} "
            f"upserted={self.upserted_count} "
            f"deleted_stale={len(self.deleted_stale_ids)}"
        )


def list_existing_chunk_ids(pinecone_index, source_doc_id: str, namespace: str) -> set[str]:
    prefix = f"{source_doc_id}{CHUNK_ID_SEPARATOR}"
    existing: set[str] = set()
    for id_batch in pinecone_index.list(prefix=prefix, namespace=namespace):
        existing.update(id_batch)
    return existing


def delete_stale_chunks(
    pinecone_index, 
    source_doc_id: str,
    current_ids: set[str], 
    namespace: str
) -> list[str]:
    
    existing_ids = list_existing_chunk_ids(pinecone_index, source_doc_id, namespace)
    stale_ids = existing_ids - current_ids
    if stale_ids:
        pinecone_index.delete(ids=list(stale_ids), namespace=namespace)
    return sorted(stale_ids)


def upsert_chunks(
    vectorstore: PineconeVectorStore,
    chunks: list[Document],
    source_doc_id: str
) -> list[str]:
    
    ids = [build_chunk_id(source_doc_id, c.page_content) for c in chunks]
    vectorstore.add_documents(documents=chunks, ids=ids)
    return ids


def reindex_document(
    vectorstore, pinecone_index, chunks, source_doc_id: str, namespace: str
) -> ReindexReport:
    current_ids = upsert_chunks(vectorstore, chunks, source_doc_id)
    deleted_ids = delete_stale_chunks(
        pinecone_index, source_doc_id, set(current_ids), namespace
    )
    return ReindexReport(
        source_doc_id=source_doc_id,
        upserted_count=len(current_ids),
        upserted_ids=current_ids,
        deleted_stale_ids=deleted_ids,
    )