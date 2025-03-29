"""Storage provider implementations.

This module provides concrete implementations of the StorageProvider interface.
"""

PROVIDER_MODULES = {
    "ChromaStorageProvider": ".chroma",
    "LocalStorageProvider": ".local",
    "DBStorageProvider": ".db",
    "ObjectStoreProvider": ".object_store",
    "SupabaseStorageProvider": ".supabase",
    "SQLiteStorageProvider": ".sqlite",
    "PineconeStorageProvider": ".pinecone",
    "RestStorageProvider": ".rest",
}

__all__ = list(PROVIDER_MODULES.keys())
