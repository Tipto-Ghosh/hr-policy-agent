from __future__ import annotations
import re
import time
from pathlib import Path

from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from pinecone import Pinecone, ServerlessSpec
from src.hr_agent.core.settings import get_settings
from src.hr_agent.ingest.metadata import(
    attach_source_doc_id,
    compute_source_doc_id,
    enrich_chunks,
)
from src.hr_agent.ingest.index  import reindex_document


HEADERS_TO_SPLIT_ON = [
    ("#", "Section"),
    ("##", "SubSection"),
    ("###", "SubSubSection"),
    ("####", "SubSubSubSection"),
]
HEADER_PATTERN = r"(?i)gesci\s*\n?\s*Founded by UN ICT Task Force"
MAX_CHUNK_SIZE = 2000


def load_document(path: Path) -> list[Document]:
    docs = UnstructuredMarkdownLoader(str(path)).load()
    for doc in docs:
        doc.page_content = re.sub(HEADER_PATTERN, "", doc.page_content).strip()
    return docs


def txt_to_markdown(text: str) -> str:
    lines, out = text.split("\n"), []
    for line in lines:
        s = line.strip()
        if not s:
            out.append(""); continue
        if re.match(r'^\d+\.?\s+[A-Z][A-Z\s,&]+$', s) and len(s) < 80:
            out.append(f"\n# {s}\n")
        elif re.match(r'^\d+\.\d+\s+[A-Z]', s) and len(s) < 100:
            out.append(f"\n## {s}\n")
        elif re.match(r'^\d+\.\d+\.\d+\s+[A-Z]', s) and len(s) < 120:
            out.append(f"\n### {s}\n")
        elif re.match(r'^\d+\.\d+\.\d+\.\d+\s+[A-Z]', s) and len(s) < 120:
            out.append(f"\n#### {s}\n")
        elif s.isupper() and len(s) < 80 and len(s.split()) <= 10:
            out.append(f"\n# {s}\n")
        elif s.istitle() and len(s) < 80 and not s.endswith('.') and len(s.split()) <= 8:
            out.append(f"\n## {s}\n")
        else:
            out.append(s)
    return "\n".join(out)


def chunk_markdown(md_text: str) -> list[Document]:
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    ).split_text(md_text)


def split_large_chunks(chunks, max_size=MAX_CHUNK_SIZE) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_size, chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    result = []
    for chunk in chunks:
        if len(chunk.page_content) <= max_size:
            result.append(chunk); continue
        for i, sub in enumerate(splitter.split_text(chunk.page_content)):
            result.append(Document(
                page_content=sub,
                metadata={**chunk.metadata, "sub_chunk_index": i},
            ))
    return result


def get_embedding_model() -> HuggingFaceEmbeddings:
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model_name,
        encode_kwargs={"normalize_embeddings": True},
    )


def ensure_index(pc: Pinecone, dim: int, index_name: str) -> None:
    existing = [i["name"] for i in pc.list_indexes()]
    if index_name in existing:
        return
    pc.create_index(
        name=index_name, dimension=dim, metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(index_name)["ready"]:
        print("Waiting for index to be ready...")
        time.sleep(1)


def run_pipeline(markdown_path: Path | None = None) -> None:
    settings = get_settings()
    markdown_path = markdown_path or (
        settings.data_processed_dir / "hr_policy.md"
    )

    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is not set")

    source_doc_id = compute_source_doc_id(markdown_path)
    print(f"[pipeline] source_doc_id = {source_doc_id}")


    docs = load_document(markdown_path)
    md_text = txt_to_markdown(docs[0].page_content)
    chunks = chunk_markdown(md_text)

    # Enrich with doc-level + breadcrumb metadata 
    enriched = enrich_chunks(
        chunks,
        source_doc_id=source_doc_id,
        extra_metadata={
            "source": "GESCI_HRPPM_2018",
            "document_type": "HR Policy Manual",
            "organization": "GESCI",
            "year": "2018",
        },
    )
    final_chunks = split_large_chunks(enriched, max_size=MAX_CHUNK_SIZE)
    attach_source_doc_id(final_chunks, source_doc_id)
    print(f"[pipeline] {len(final_chunks)} final chunks")

    # Embeddings + Pinecone
    embedding = get_embedding_model()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    ensure_index(
        pc,
        dim=len(embedding.embed_query("dimension probe")),
        index_name=settings.pinecone_index_name,
    )
    pinecone_index = pc.Index(settings.pinecone_index_name)

    vectorstore = PineconeVectorStore(
        index=pinecone_index,
        embedding=embedding,
        namespace=settings.pinecone_namespace,
    )

    # Versioning-aware upsert
    report = reindex_document(
        vectorstore=vectorstore,
        pinecone_index=pinecone_index,
        chunks=final_chunks,
        source_doc_id=source_doc_id,
        namespace=settings.pinecone_namespace,
    )
    print(f"[pipeline] {report.summary()}")
