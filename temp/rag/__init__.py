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
    EmbeddingError,
    GenerationError,
    PipelineError,
    PipelineStageError,
    RerankingError,
    VectorStoreError,
)
from pepperpy.rag.pipeline.builder import RAGPipeline, RAGPipelineBuilder
from pepperpy.rag.pipeline.stages import (
    GenerationStage,
    GenerationStageConfig,
    RerankingStage,
    RerankingStageConfig,
    RetrievalStage,
    RetrievalStageConfig,
)
from pepperpy.rag.providers.embedding import (
    BaseEmbeddingProvider,
    MockEmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from pepperpy.rag.providers.generation import (
    BaseGenerationProvider,
    MockGenerationProvider,
    OpenAIGenerationProvider,
)
from pepperpy.rag.providers.reranking import (
    BaseRerankingProvider,
    CrossEncoderProvider,
    MockRerankingProvider,
)
from pepperpy.rag.storage import (
    ChromaVectorStore,
    FileVectorStore,
    MemoryVectorStore,
    VectorStore,
)

__all__ = [
    # Core types
    "DocumentChunk",
    "VectorStore",
    # Pipeline
    "RAGPipeline",
    "RAGPipelineBuilder",
    # Stage classes
    "RetrievalStage",
    "RerankingStage",
    "GenerationStage",
    # Stage configs
    "RetrievalStageConfig",
    "RerankingStageConfig",
    "GenerationStageConfig",
    # Provider base classes
    "BaseEmbeddingProvider",
    "BaseRerankingProvider",
    "BaseGenerationProvider",
    # Embedding providers
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    # Reranking providers
    "MockRerankingProvider",
    "CrossEncoderProvider",
    # Generation providers
    "MockGenerationProvider",
    "OpenAIGenerationProvider",
    # Vector stores
    "MemoryVectorStore",
    "FileVectorStore",
    "ChromaVectorStore",
    # Errors
    "EmbeddingError",
    "GenerationError",
    "PipelineError",
    "PipelineStageError",
    "RerankingError",
    "VectorStoreError",
]
