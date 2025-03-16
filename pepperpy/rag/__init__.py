"""RAG (Retrieval Augmented Generation) module.

This module provides functionality for implementing RAG systems,
including document processing, retrieval, and generation.
"""

from pepperpy.rag.document import (
    TextChunker,
    TextCleaner,
    TextLoader,
    chunk_document,
    load_text_document,
)
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
from pepperpy.rag.pipeline import (
    PipelineConfig,
    RAGPipeline,
    create_default_pipeline,
    create_metadata_focused_pipeline,
    create_simple_pipeline,
    process_document,
    process_documents,
)
from pepperpy.rag.retrieval import (
    RetrievalConfig,
    Retriever,
    retrieve_documents,
)
from pepperpy.rag.stages import (
    GenerationStage,
    GenerationStageConfig,
    RerankingStage,
    RerankingStageConfig,
    RetrievalStage,
    RetrievalStageConfig,
    StageConfig,
)
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
    "load_text_document",
    "chunk_document",
    # Retrieval functionality
    "Retriever",
    "RetrievalConfig",
    "retrieve_documents",
    # Pipeline
    "PipelineConfig",
    "RAGPipeline",
    "create_default_pipeline",
    "create_simple_pipeline",
    "create_metadata_focused_pipeline",
    "process_document",
    "process_documents",
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
