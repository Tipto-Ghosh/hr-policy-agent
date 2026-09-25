from pinecone import Pinecone
from src.hr_agent.core.settings import get_settings
from src.hr_agent.ingest.ingest import run_pipeline

run_pipeline()

s = get_settings()
pc = Pinecone(api_key=s.pinecone_api_key)
index = pc.Index(s.pinecone_index_name)

stats = index.describe_index_stats()
print("Total vectors :", stats.total_vector_count)
print("Dimension     :", stats.dimension)
print("Namespaces    :")
for ns, info in stats.namespaces.items():
    print(f"  - {ns or '<default>':<40} {info.vector_count} vectors")
