"""RAG (Retrieval Augmented Generation) module.

This module provides functionality for building and using RAG systems.
It includes components for document storage, retrieval, reranking,
and generation, along with a flexible pipeline system.

Example usage:
    ```python
    from pepperpy.rag import RAGPipelineBuilder
    from pepperpy.rag.providers.embedding import OpenAIEmbeddingProvider
    from pepperpy.rag.providers.reranking import CrossEncoderProvider
    from pepperpy.rag.providers.generation import OpenAIGenerationProvider
    from pepperpy.rag.storage import ChromaVectorStore

    # Initialize components
    vector_store = ChromaVectorStore(...)
    embedding_provider = OpenAIEmbeddingProvider(...)
    reranker = CrossEncoderProvider(...)
    generator = OpenAIGenerationProvider(...)

    # Build pipeline
    pipeline = (
        RAGPipelineBuilder()
        .with_retrieval(vector_store, embedding_provider)
        .with_reranking(reranker)
        .with_generation(generator)
        .build()
    )

    # Process query
    result = await pipeline.process("What is the capital of France?")
    print(result["response"])
    ```
"""

from pepperpy.rag.document.core import DocumentChunk
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

# Try to import pipeline components, but don't fail if dependencies are missing
try:
    from pepperpy.rag.pipeline.builder import RAGPipeline, RAGPipelineBuilder

    _has_pipeline = True
except ImportError:
    _has_pipeline = False

# Import pipeline stages with error handling for missing components
try:
    from pepperpy.rag.pipeline.stages import (
        GenerationStage,
        RerankingStage,
        RetrievalStage,
    )

    _has_stages = True
except ImportError:
    _has_stages = False

# Import embedding providers
try:
    from pepperpy.rag.providers.embedding import (
        BaseEmbeddingProvider,
    )

    _has_embedding = True
except ImportError:
    _has_embedding = False

# Import vector stores with error handling for missing components
try:
    from pepperpy.rag.storage import (
        VectorStore,
    )

    _has_storage = True
except ImportError:
    _has_storage = False

# Define exports
__all__ = [
    # Core
    "DocumentChunk",
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
]

# Add pipeline exports if available
if _has_pipeline:
    __all__.extend([
        "RAGPipeline",
        "RAGPipelineBuilder",
    ])

# Add stage exports if available
if _has_stages:
    __all__.extend([
        "GenerationStage",
        "RerankingStage",
        "RetrievalStage",
    ])

# Add embedding exports if available
if _has_embedding:
    __all__.extend([
        "BaseEmbeddingProvider",
    ])

# Add storage exports if available
if _has_storage:
    __all__.extend([
        "VectorStore",
    ])
