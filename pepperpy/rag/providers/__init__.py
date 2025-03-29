"""RAG providers."""

PROVIDER_MODULES = {
    "sqlite": "pepperpy.rag.providers.sqlite",
    "qdrant": "pepperpy.rag.providers.qdrant",
    "pinecone": "pepperpy.rag.providers.pinecone",
    "milvus": "pepperpy.rag.providers.milvus",
    "lancedb": "pepperpy.rag.providers.lancedb",
    "epsilla": "pepperpy.rag.providers.epsilla",
    "tiny_vector": "pepperpy.rag.providers.tiny_vector",
    "hyperdb": "pepperpy.rag.providers.hyperdb",
    "vqlite": "pepperpy.rag.providers.vqlite",
    "chroma": "pepperpy.rag.providers.chroma",
    "memory": "pepperpy.rag.providers.memory",
    "annoy": "pepperpy.rag.providers.annoy",
    "supabase": "pepperpy.rag.providers.supabase",
    "postgres": "pepperpy.rag.providers.postgres",
}

PROVIDER_CLASSES = {
    "sqlite": "SQLiteRAGProvider",
    "qdrant": "QdrantProvider",
    "pinecone": "PineconeProvider",
    "milvus": "MilvusProvider",
    "lancedb": "LanceDBProvider",
    "epsilla": "EpsillaProvider",
    "tiny_vector": "TinyVectorProvider",
    "hyperdb": "HyperDBProvider",
    "vqlite": "VQLiteProvider",
    "chroma": "ChromaProvider",
    "memory": "InMemoryProvider",
    "annoy": "AnnoyRAGProvider",
    "supabase": "SupabaseRAGProvider",
    "postgres": "PostgresRAGProvider",
}

DEFAULT_PROVIDER = "sqlite"

__all__ = [
    "DEFAULT_PROVIDER",
    "PROVIDER_MODULES",
    "PROVIDER_CLASSES",
]
