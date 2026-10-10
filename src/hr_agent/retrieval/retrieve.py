from __future__ import annotations
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from hr_agent.core.settings import get_settings

__all__ = [
    "get_embedding_model",
    "get_vectorstore",
    "get_retriever",
]

@lru_cache()
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Get the embedding model."""
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name = settings.embedding_model_name,
        model_kwargs = settings.embedding_model_kwargs,
        encode_kwargs = settings.embedding_model_encode_kwargs,
    )
    

def get_vectorstore(
   index_name: str | None = None,
   namespace: str | None = None
) -> PineconeVectorStore:
    """Connect to the Pinecone index and return a vectorstore object."""
    settings = get_settings()
    if not settings.pinecone_api_key:
        raise ValueError("Pinecone API key is not set in settings.")
    
    resolved_index = index_name or settings.pinecone_index_name
    resolved_namespace = namespace or settings.pinecone_namespace
    
    pc = Pinecone(
        api_key = settings.pinecone_api_key
    )
    
    index = pc.Index(resolved_index)

    return PineconeVectorStore(
        index = index,
        embedding = get_embedding_model(),
        namespace = resolved_namespace
    )
    
    
def get_retriever(
    k: int = 5,
    index_name: str | None = None,
    namespace: str | None = None,
    **search_overrides,
):
    """
    Return a LangChain retriever object for the Pinecone vectorstore.
    
    Args:
        k: Number of results to return.
        index_name: Optional Pinecone index name. If not provided, will use the
            default from settings.
        namespace: Optional Pinecone namespace. If not provided, will use the
            default from settings.
        **search_overrides: Additional keyword arguments to pass to the retriever's
            search method (e.g., `filter={"year": 2023}`, `include_metadata`, etc.).
    """
    settings = get_settings()
    resolved_index = index_name or settings.pinecone_index_name
    resolved_namespace = namespace or settings.pinecone_namespace
    
    vectorstore = get_vectorstore(
        index_name = resolved_index,
        namespace = resolved_namespace
    )
    search_kwargs = {
        **search_overrides,
        "k": k,
        "namespace": resolved_namespace,
    }
    return vectorstore.as_retriever(search_kwargs=search_kwargs)