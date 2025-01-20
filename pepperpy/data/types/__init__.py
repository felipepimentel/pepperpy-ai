"""Types module for Pepperpy data."""

from .protocols import (
    Embeddable,
    Chunkable,
    SimilarityComparable,
    Storable,
    Indexable,
    Cacheable,
)

from .storage import (
    StorageBackend,
    VectorStore,
    DocumentStore,
    MemoryStore,
    Cache,
)

__all__ = [
    # Storage protocols
    "StorageBackend",
    "VectorStore",
    "DocumentStore",
    "MemoryStore",
    "Cache",
    
    # Data protocols
    "Embeddable",
    "Chunkable",
    "SimilarityComparable",
    "Storable",
    "Indexable",
    "Cacheable",
] 