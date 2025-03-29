"""Storage providers."""

PROVIDER_MODULES = {
    "local": "pepperpy.storage.providers.local",
    "db": "pepperpy.storage.providers.db",
    "object": "pepperpy.storage.providers.object_store",
    "chroma": "pepperpy.storage.providers.chroma",
    "rest": "pepperpy.storage.providers.rest",
    "sqlite": "pepperpy.storage.providers.sqlite",
    "supabase": "pepperpy.storage.providers.supabase",
}

PROVIDER_CLASSES = {
    "local": "LocalProvider",
    "db": "DBProvider",
    "object": "ObjectStoreProvider",
    "chroma": "ChromaStorageProvider",
    "rest": "RestProvider",
    "sqlite": "SQLiteProvider",
    "supabase": "SupabaseProvider",
}

DEFAULT_PROVIDER = "local"

__all__ = [
    "DEFAULT_PROVIDER",
    "PROVIDER_MODULES",
    "PROVIDER_CLASSES",
]
