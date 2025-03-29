"""RAG provider implementations.

This module contains implementations of the RAG provider interface
for different storage and retrieval systems.
"""

PROVIDER_MODULES = {
    "ChromaProvider": ".chroma",
    "InMemoryProvider": ".memory",
    "SQLiteRAGProvider": ".sqlite",
    "TinyVectorProvider": ".tiny_vector",
    "AnnoyProvider": ".annoy",
    "PineconeProvider": ".pinecone",
    "OasysProvider": ".oasys",
    "VectorDBProvider": ".vectordb",
    "SupabaseProvider": ".supabase",
    "FaissProvider": ".faiss",
}

__all__ = list(PROVIDER_MODULES.keys())

# Set default provider
DEFAULT_PROVIDER = "SQLiteRAGProvider"
