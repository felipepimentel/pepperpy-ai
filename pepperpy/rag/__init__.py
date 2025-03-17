"""RAG (Retrieval Augmented Generation) module.

This module provides functionality for implementing RAG systems,
including document processing, retrieval, and generation.
"""

# Import core document processing components
from pepperpy.rag.document import (
    TextChunker,
    TextCleaner,
    TextLoader,
)

# Import interfaces
from pepperpy.rag.interfaces import (
    DocumentLoader,
    DocumentProcessor,
    DocumentStore,
    EmbeddingProvider,
    GenerationProvider,
    PipelineStage,
    RerankerProvider,
    SearchProvider,
    VectorStore,
)

# Import models
from pepperpy.rag.models import (
    # Chunking models
    ChunkingConfig,
    ChunkingStrategy,
    ChunkMetadata,
    # Document models
    Document,
    DocumentChunk,
    GenerationResult,
    Metadata,
    # Metadata models
    MetadataExtractorConfig,
    MetadataType,
    RerankingResult,
    # Result models
    RetrievalResult,
    # Scored chunk
    ScoredChunk,
    # Transformation models
    TransformationConfig,
    TransformationType,
)

# Import retrieval components
from pepperpy.rag.retrieval import (
    RetrievalConfig,
    Retriever,
    retrieve_documents,
)

# Import pipeline stages
from pepperpy.rag.stages import (
    GenerationStage,
    GenerationStageConfig,
    RerankingStage,
    RerankingStageConfig,
    RetrievalStage,
    RetrievalStageConfig,
    StageConfig,
)

# Import utility functions
from pepperpy.rag.utils import (
    calculate_text_statistics,
    clean_markdown_formatting,
    clean_text,
    extract_html_metadata,
    remove_html_tags,
    split_text_by_char,
    split_text_by_separator,
)

__all__ = [
    # Core document types
    "Document",
    "DocumentChunk",
    "Metadata",
    "ScoredChunk",
    # Chunking models
    "ChunkingConfig",
    "ChunkingStrategy",
    "ChunkMetadata",
    # Transformation models
    "TransformationConfig",
    "TransformationType",
    # Metadata models
    "MetadataExtractorConfig",
    "MetadataType",
    # Interfaces
    "DocumentLoader",
    "DocumentProcessor",
    "DocumentStore",
    "EmbeddingProvider",
    "GenerationProvider",
    "PipelineStage",
    "RerankerProvider",
    "SearchProvider",
    "VectorStore",
    # Document functionality
    "TextLoader",
    "TextChunker",
    "TextCleaner",
    # Retrieval functionality
    "Retriever",
    "RetrievalConfig",
    "retrieve_documents",
    # Pipeline stages
    "StageConfig",
    "RetrievalStage",
    "RetrievalStageConfig",
    "RetrievalResult",
    "RerankingStage",
    "RerankingStageConfig",
    "RerankingResult",
    "GenerationStage",
    "GenerationStageConfig",
    "GenerationResult",
    # Utility functions
    "calculate_text_statistics",
    "clean_markdown_formatting",
    "clean_text",
    "extract_html_metadata",
    "remove_html_tags",
    "split_text_by_char",
    "split_text_by_separator",
]
