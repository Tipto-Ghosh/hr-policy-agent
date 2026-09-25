from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

CHUNK_ID_SEPARATOR = "__"


def build_chunk_id(source_doc_id: str, chunk_index: int) -> str:
    content_hash = hashlib.sha256(str(chunk_index).encode()).hexdigest()[:16]
    return f"{source_doc_id}{CHUNK_ID_SEPARATOR}{content_hash}"

@dataclass
class ReindexReport:
    source_doc_id: str
    upserted_count: int
    unchanged_or_upserted_ids: list[str] = field(default_factory=list)
    deleted_stale_ids: list[str] = field(default_factory=list)
 
    def summary(self) -> str:
        return (
            f"source_doc_id={self.source_doc_id} "
            f"upserted={self.upserted_count} "
            f"deleted_stale={len(self.deleted_stale_ids)}"
        )

def list_existing_chunk_ids(pinecone_index, source_doc_id: str, namespace: str) -> set[str]:
    """
    List every vector ID currently in the Pinecone index under this document's
    prefix.
    
    Returns an empty set if nothing exists yet for this source_doc_id.
    """
    prefix = f"{source_doc_id}{CHUNK_ID_SEPARATOR}"
    existing = set()
    
    for id_batch in pinecone_index.list(prefix=prefix, namespace=namespace):
        existing.update(id_batch)
    
    return existing

def delete_stale_chunks(pinecone_index,source_doc_id: str,current_ids: set[str],namespace: str) -> list[str]:
    """
    Delete any vector under this source_doc_id's prefix that is NOT in
    `current_ids` — i.e. left over from a previous version of the document
    whose content has since changed or been removed.
    """
    existing_ids = list_existing_chunk_ids(
        pinecone_index, source_doc_id, namespace
    )
    stale_ids = existing_ids - current_ids
    if stale_ids:
        pinecone_index.delete(ids=list(stale_ids), namespace=namespace)
    return sorted(stale_ids)

def upsert_chunks(
    vectorstore: PineconeVectorStore,
    chunks: list[Document],
    source_doc_id: str,
) -> list[str]:
    """
    Upsert `chunks` (which must already have `source_doc_id` in their
    metadata — see ingestion/metadata.py:attach_source_doc_id) using
    deterministic, content-addressed IDs.
 
    Uses `add_documents(..., ids=...)`, which Pinecone treats as an upsert:
    an existing ID's vector+metadata is overwritten, not duplicated.
    """
    ids = [build_chunk_id(source_doc_id, chunk.page_content) for chunk in chunks]
    vectorstore.add_documents(documents=chunks, ids=ids)
    return ids

def reindex_chunks(vectorstore, pinecone_index, chunks, source_doc_id, namespace) -> ReindexReport:
    """
    Full versioning-aware ingestion of one document's chunks: 
    upsert current chunks, delete any stale chunks.
    """
    current_ids = upsert_chunks(vectorstore, chunks, source_doc_id)
    deleted_ids = delete_stale_chunks(
        pinecone_index, source_doc_id, set(current_ids), namespace
    )
    return ReindexReport(
        source_doc_id=source_doc_id,
        upserted_count=len(current_ids),
        unchanged_or_upserted_ids=current_ids,
        deleted_stale_ids=deleted_ids
    )
     