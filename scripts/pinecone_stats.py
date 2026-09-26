from __future__ import annotations
from pathlib import Path
from pinecone import Pinecone
from hr_agent.core.settings import get_settings
from hr_agent.ingest.metadata import compute_source_doc_id

def main():
    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    stats = index.describe_index_stats()
    
    print("Pinecone Index Stats:")
    print(f"Index         : {settings.pinecone_index_name}")
    print(f"Dimension     : {stats.dimension}")
    print(f"Total vectors : {stats.total_vector_count}")
    print("Namespaces:")
    for ns, info in stats.namespaces.items():
        print(f"  - {ns or '<default>':<42} {info.vector_count}")

    target_ns = settings.pinecone_namespace
    ns_info = stats.namespaces.get(target_ns)
    print(
        f"\nNamespace '{target_ns}': "
        f"{ns_info.vector_count if ns_info else 0} vectors"
    )

    md = Path(settings.data_processed_dir) / "hr_policy.md"
    if md.exists():
        sid = compute_source_doc_id(md)
        ids: set[str] = set()
        for batch in index.list(prefix=f"{sid}__", namespace=target_ns):
            ids.update(batch)
        print(f"Vectors for source_doc_id={sid}: {len(ids)}")
        
if __name__ == "__main__":
    main()