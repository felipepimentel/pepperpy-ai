"""RAG Pipeline implementation.

This module provides the core implementation of the RAG pipeline system,
which orchestrates the retrieval, reranking, and generation stages.

Note:
    This module uses the unified pipeline framework from `pepperpy.core.pipeline`.
    For new implementations, use the adapter pattern from `pepperpy.rag.pipeline.adapter`.

Example:
    >>> from pepperpy.rag.pipeline.adapter import RAGPipelineBuilderAdapter
    >>> from pepperpy.rag.stages import RetrievalStage, GenerationStage
    >>> from pepperpy.core.pipeline.base import PipelineContext
    >>>
    >>> # Create stages
    >>> retrieval = RetrievalStage(...)
    >>> generation = GenerationStage(...)
    >>>
    >>> # Create pipeline using the adapter
    >>> builder = RAGPipelineBuilderAdapter()
    >>> pipeline = await builder.create_simple_pipeline(
    ...     retrieval_stage=retrieval,
    ...     generation_stage=generation,
    ...     name="my_rag"
    ... )
    >>>
    >>> # Execute pipeline
    >>> context = PipelineContext()
    >>> result = await pipeline.execute(
    ...     "What is RAG?",
    ...     context
    ... )
    >>> print(result)  # Generated response
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.errors import PepperPyError
from pepperpy.rag.models import (
    Document,
    RerankingResult,
)
from pepperpy.rag.stages import (
    GenerationStage,
    GenerationStageConfig,
    RerankingStage,
    RerankingStageConfig,
    RetrievalStage,
    RetrievalStageConfig,
)

# Import interfaces

# Type variables
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


@dataclass
class PipelineConfig:
    """Configuration for a RAG pipeline.

    This class defines the configuration for a RAG pipeline, including
    parameters for the retrieval, reranking, and generation stages.

    Note:
        This configuration class is used by both the legacy implementation
        and the new unified framework through the adapter pattern.

    Example:
        >>> from pepperpy.rag.pipeline.adapter import RAGPipelineBuilderAdapter
        >>> from pepperpy.rag.stages import RetrievalStage, GenerationStage
        >>>
        >>> # Create stages with configs
        >>> retrieval_config = RetrievalStageConfig(...)
        >>> generation_config = GenerationStageConfig(...)
        >>>
        >>> # Create pipeline config
        >>> config = PipelineConfig(
        ...     name="my_rag",
        ...     description="Custom RAG pipeline",
        ...     retrieval_config=retrieval_config,
        ...     generation_config=generation_config,
        ... )
        >>>
        >>> # Create pipeline with config
        >>> builder = RAGPipelineBuilderAdapter()
        >>> pipeline = await builder.create_simple_pipeline(
        ...     retrieval_stage=RetrievalStage(retrieval_config),
        ...     generation_stage=GenerationStage(generation_config),
        ...     name=config.name,
        ... )
    """

    # General pipeline parameters
    name: str = "default"
    description: str = "Default RAG pipeline configuration"

    # Stage configurations
    retrieval_config: Optional[RetrievalStageConfig] = None
    reranking_config: Optional[RerankingStageConfig] = None
    generation_config: Optional[GenerationStageConfig] = None

    # Additional parameters
    params: Dict[str, Any] = field(default_factory=dict)


class RAGPipeline:
    """RAG pipeline implementation.

    This class implements a RAG pipeline, which orchestrates the retrieval,
    reranking, and generation stages of the RAG process.
    """

    def __init__(
        self,
        retrieval_stage: Optional[RetrievalStage] = None,
        reranking_stage: Optional[RerankingStage] = None,
        generation_stage: Optional[GenerationStage] = None,
        config: Optional[PipelineConfig] = None,
    ):
        """Initialize the RAG pipeline.

        Args:
            retrieval_stage: The retrieval stage
            reranking_stage: The reranking stage
            generation_stage: The generation stage
            config: The pipeline configuration
        """
        self.retrieval_stage = retrieval_stage
        self.reranking_stage = reranking_stage
        self.generation_stage = generation_stage
        self.config = config or PipelineConfig()

    async def process_query(self, query: str) -> str:
        """Process a query using the RAG pipeline.

        Args:
            query: The query to process

        Returns:
            The generated response

        Raises:
            PepperPyError: If processing fails
        """
        # Execute the retrieval stage
        if not self.retrieval_stage:
            raise PepperPyError("No retrieval stage configured")

        retrieval_result = await self.retrieval_stage.process(query)

        # Execute the reranking stage if available
        if self.reranking_stage:
            reranking_result = await self.reranking_stage.process(retrieval_result)
        else:
            # Create a simple reranking result with the retrieval chunks
            reranking_result = RerankingResult(
                chunks=retrieval_result.chunks,
                query=query,
                original_chunks=retrieval_result.chunks,
                metadata={},
            )

        # Execute the generation stage
        if not self.generation_stage:
            raise PepperPyError("No generation stage configured")

        generation_result = await self.generation_stage.process(reranking_result)

        return generation_result.text


async def create_simple_pipeline(
    retrieval_stage: RetrievalStage,
    generation_stage: GenerationStage,
) -> RAGPipeline:
    """Create a simple RAG pipeline with retrieval and generation stages.

    Args:
        retrieval_stage: The retrieval stage
        generation_stage: The generation stage

    Returns:
        The created RAG pipeline
    """
    return RAGPipeline(
        retrieval_stage=retrieval_stage,
        generation_stage=generation_stage,
    )


async def create_default_pipeline(
    retrieval_stage: RetrievalStage,
    reranking_stage: RerankingStage,
    generation_stage: GenerationStage,
) -> RAGPipeline:
    """Create a default RAG pipeline with all stages.

    Args:
        retrieval_stage: The retrieval stage
        reranking_stage: The reranking stage
        generation_stage: The generation stage

    Returns:
        The created RAG pipeline
    """
    return RAGPipeline(
        retrieval_stage=retrieval_stage,
        reranking_stage=reranking_stage,
        generation_stage=generation_stage,
    )


async def create_metadata_focused_pipeline(
    retrieval_stage: RetrievalStage,
    generation_stage: GenerationStage,
) -> RAGPipeline:
    """Create a metadata-focused RAG pipeline.

    Args:
        retrieval_stage: The retrieval stage
        generation_stage: The generation stage

    Returns:
        The created RAG pipeline
    """
    # Configure the retrieval stage to focus on metadata
    if hasattr(retrieval_stage.config, "params"):
        retrieval_stage.config.params["metadata_weight"] = 0.7

    return RAGPipeline(
        retrieval_stage=retrieval_stage,
        generation_stage=generation_stage,
    )


async def process_document(
    document: Document,
    pipeline: RAGPipeline,
    query: str,
) -> str:
    """Process a document using a RAG pipeline.

    Args:
        document: The document to process
        pipeline: The RAG pipeline to use
        query: The query to process

    Returns:
        The generated response
    """
    # Add the document to the retrieval stage's store
    if not pipeline.retrieval_stage:
        raise PepperPyError("No retrieval stage configured")

    # Add document to the document store
    # This assumes document_store has an add method, which we'll need to verify
    if hasattr(pipeline.retrieval_stage, "document_store") and hasattr(
        pipeline.retrieval_stage.document_store, "add_document"
    ):
        await pipeline.retrieval_stage.document_store.add_document(document)
    else:
        raise PepperPyError("Document storage not supported by the retrieval stage")

    # Process the query
    return await pipeline.process_query(query)


async def process_documents(
    documents: List[Document],
    pipeline: RAGPipeline,
    query: str,
) -> str:
    """Process multiple documents using a RAG pipeline.

    Args:
        documents: The documents to process
        pipeline: The RAG pipeline to use
        query: The query to process

    Returns:
        The generated response
    """
    # Add the documents to the retrieval stage's store
    if not pipeline.retrieval_stage:
        raise PepperPyError("No retrieval stage configured")

    # Add each document to the document store
    if hasattr(pipeline.retrieval_stage, "document_store") and hasattr(
        pipeline.retrieval_stage.document_store, "add_document"
    ):
        for document in documents:
            await pipeline.retrieval_stage.document_store.add_document(document)
    else:
        raise PepperPyError("Document storage not supported by the retrieval stage")

    # Process the query
    return await pipeline.process_query(query)
