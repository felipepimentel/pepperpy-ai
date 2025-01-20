"""Dynamic sources module for data processing and management."""

from .services import DataRESTService, DataWebSocketService
from .types import (
    Embeddable,
    Chunkable,
    SimilarityComparable,
    Storable,
    Indexable,
    Cacheable,
)
from .pipeline import (
    # Ingestion
    IngestError,
    Source,
    Sink,
    IngestManager,
    FileSource,
    FileSink,
    # Updates
    UpdateError,
    Store,
    UpdateManager,
    FileStore,
    # Vector linking
    LinkerError,
    VectorLinker,
)

__all__ = [
    # Services
    "DataRESTService",
    "DataWebSocketService",
    # Types
    "Embeddable",
    "Chunkable",
    "SimilarityComparable",
    "Storable",
    "Indexable",
    "Cacheable",
    # Pipeline - Ingestion
    "IngestError",
    "Source",
    "Sink",
    "IngestManager",
    "FileSource",
    "FileSink",
    # Pipeline - Updates
    "UpdateError",
    "Store",
    "UpdateManager",
    "FileStore",
    # Pipeline - Vector linking
    "LinkerError",
    "VectorLinker",
]
