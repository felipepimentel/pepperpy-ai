"""Public API for the RAG module.

This module provides the public API for Retrieval-Augmented Generation (RAG),
including document processing, vector storage, and query processing.
"""

from pepperpy.rag.core import (
    RAGManager,
    add_document,
    get_rag_manager,
    query,
    search,
)
from pepperpy.rag.document.core import Document, DocumentChunk, Metadata
from pepperpy.rag.errors import (
    DocumentError,
    DocumentLoadError,
    DocumentProcessError,
    GenerationError,
    PipelineError,
    PipelineStageError,
    QueryError,
    RAGError,
    RetrievalError,
    StorageError,
    VectorStoreError,
)
from pepperpy.rag.pipeline.core import (
    Pipeline,
    PipelineManager,
    PipelineStage,
    Query,
    QueryResult,
    get_pipeline_manager,
)
from pepperpy.rag.storage.core import (
    ScoredChunk,
    VectorEmbedding,
    VectorStore,
    VectorStoreManager,
    get_vector_store_manager,
)

# Define public API
__all__ = [
    # Core
    "RAGManager",
    "get_rag_manager",
    "add_document",
    "query",
    "search",
    # Document
    "Document",
    "DocumentChunk",
    "Metadata",
    # Errors
    "RAGError",
    "DocumentError",
    "DocumentLoadError",
    "DocumentProcessError",
    "StorageError",
    "VectorStoreError",
    "PipelineError",
    "PipelineStageError",
    "QueryError",
    "RetrievalError",
    "GenerationError",
    # Pipeline
    "Pipeline",
    "PipelineManager",
    "PipelineStage",
    "Query",
    "QueryResult",
    "get_pipeline_manager",
    # Storage
    "VectorStore",
    "VectorStoreManager",
    "VectorEmbedding",
    "ScoredChunk",
    "get_vector_store_manager",
]
