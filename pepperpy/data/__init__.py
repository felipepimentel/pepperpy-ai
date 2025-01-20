"""Data module for Pepperpy."""

from .types import (
    # Storage protocols
    StorageBackend,
    VectorStore,
    DocumentStore,
    MemoryStore,
    Cache,
    
    # Data protocols
    Embeddable,
    Chunkable,
    SimilarityComparable,
    Storable,
    Indexable,
    Cacheable,
)

from .stores import (
    DataStore,
    DataStoreError,
    InMemoryStore,
    SQLiteStore,
)

from .vector.embeddings import (
    EmbeddingModel,
    OpenAIEmbeddingModel,
)

from .vector.indexer import (
    VectorIndex,
    IndexError,
    SearchResult,
    IndexManager,
)

from .processing.transformer import (
    TransformError,
    Transformer,
    TransformManager,
    TextNormalizer,
    TextChunker,
    TextCleaner,
)

from .processing.validator import (
    ValidationError,
    Validator,
    ValidationManager,
    TextLengthValidator,
    TextContentValidator,
    TextFormatValidator,
)

from .dynamic_sources.base import (
    AlgorithmError,
    Algorithm,
    BaseAlgorithm,
    AlgorithmChain,
)

from .dynamic_sources.chunking import (
    ChunkingError,
    TextChunkingAlgorithm,
)

from .dynamic_sources.cleaning import (
    CleaningError,
    TextCleaningAlgorithm,
)

from .dynamic_sources.ingest import (
    IngestError,
    Source,
    Sink,
    IngestManager,
    FileSource,
    FileSink,
)

from .dynamic_sources.update import (
    UpdateError,
    Store,
    UpdateManager,
    FileStore,
)

from .dynamic_sources.vector_linker import (
    LinkerError,
    VectorLinker,
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
    
    # Data stores
    "DataStore",
    "DataStoreError",
    "InMemoryStore",
    "SQLiteStore",
    
    # Vector embeddings
    "EmbeddingModel",
    "OpenAIEmbeddingModel",
    
    # Vector indexing
    "VectorIndex",
    "IndexError",
    "SearchResult",
    "IndexManager",
    
    # Data processing
    "TransformError",
    "Transformer",
    "TransformManager",
    "TextNormalizer",
    "TextChunker",
    "TextCleaner",
    "ValidationError",
    "Validator",
    "ValidationManager",
    "TextLengthValidator",
    "TextContentValidator",
    "TextFormatValidator",
    
    # Dynamic sources
    "AlgorithmError",
    "Algorithm",
    "BaseAlgorithm",
    "AlgorithmChain",
    "ChunkingError",
    "TextChunkingAlgorithm",
    "CleaningError",
    "TextCleaningAlgorithm",
    "IngestError",
    "Source",
    "Sink",
    "IngestManager",
    "FileSource",
    "FileSink",
    "UpdateError",
    "Store",
    "UpdateManager",
    "FileStore",
    "LinkerError",
    "VectorLinker",
]
