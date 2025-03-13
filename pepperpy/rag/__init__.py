"""RAG (Retrieval Augmented Generation) module.

This module provides functionality for implementing RAG systems,
including document processing, retrieval, and generation.
"""

from pepperpy.rag.interfaces import (
    DocumentLoader,
    DocumentProcessor,
    DocumentStore,
    DocumentTransformer,
    EmbeddingProvider,
    GenerationProvider,
    MetadataExtractor,
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
    # Transformation models
    TransformationConfig,
    TransformationType,
)
from pepperpy.rag.pipeline.core import (
    RAGPipeline,
    create_default_pipeline,
    create_metadata_focused_pipeline,
    create_simple_pipeline,
    process_document,
    process_documents,
)
from pepperpy.rag.pipeline.stages.generation import GenerationStage
from pepperpy.rag.pipeline.stages.reranking import RerankingStage
from pepperpy.rag.pipeline.stages.retrieval import RetrievalStage
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
    "DocumentTransformer",
    "EmbeddingProvider",
    "GenerationProvider",
    "MetadataExtractor",
    "PipelineStage",
    "RerankerProvider",
    "SearchProvider",
    "VectorStore",
    # Pipeline
    "RAGPipeline",
    "create_default_pipeline",
    "create_simple_pipeline",
    "create_metadata_focused_pipeline",
    "process_document",
    "process_documents",
    # Pipeline stages
    "RetrievalStage",
    "RetrievalResult",
    "RerankingStage",
    "RerankingResult",
    "GenerationStage",
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
