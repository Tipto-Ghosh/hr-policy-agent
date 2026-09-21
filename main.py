import importlib.metadata as meta
from langchain_pinecone import PineconeVectorStore

# Print installed versions
print("langchain-pinecone:", meta.version("langchain-pinecone"))
print("pinecone:", meta.version("pinecone"))

# Test the specific class that was failing
print("Import successful!")