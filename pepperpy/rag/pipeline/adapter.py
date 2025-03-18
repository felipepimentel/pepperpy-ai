"""RAG pipeline adapter for the new unified pipeline framework.

This module provides adapters to help migrate the RAG pipeline implementation
to use the new unified pipeline framework. It includes adapters for each stage
of the RAG pipeline (retrieval, reranking, generation) as well as the main
pipeline adapter and a builder for creating common pipeline configurations.

Example:
    Basic usage with a simple RAG pipeline:

    >>> from pepperpy.rag.pipeline import RAGPipeline
    >>> from pepperpy.rag.stages import RetrievalStage, GenerationStage
    >>> from pepperpy.core.pipeline.base import PipelineContext
    >>>
    >>> # Create stages
    >>> retrieval = RetrievalStage(...)
    >>> generation = GenerationStage(...)
    >>>
    >>> # Create and configure pipeline
    >>> builder = RAGPipelineBuilderAdapter()
    >>> pipeline = await builder.create_simple_pipeline(
    ...     retrieval_stage=retrieval,
    ...     generation_stage=generation,
    ...     name="my_rag_pipeline"
    ... )
    >>>
    >>> # Execute pipeline
    >>> context = PipelineContext()
    >>> result = await pipeline.execute(
    ...     "What is the capital of France?",
    ...     context
    ... )
    >>> print(result)  # Generated response using retrieved context
"""

from typing import Any, Dict, Optional

from pepperpy.core.pipeline.base import Pipeline as NewPipeline
from pepperpy.core.pipeline.base import PipelineContext, PipelineStage
from pepperpy.rag.models import (
    GenerationResult,
    RerankingResult,
    RetrievalResult,
    ScoredChunk,
)
from pepperpy.rag.pipeline.core import RAGPipeline
from pepperpy.rag.pipeline.stages import (
    GenerationStage,
    RerankingStage,
    RetrievalStage,
)


class RetrievalStageAdapter(PipelineStage[str, RetrievalResult]):
    """Adapter for the retrieval stage.

    This adapter wraps a RAG retrieval stage to make it compatible with
    the new unified pipeline framework. It converts the stage's output
    into properly scored chunks for downstream processing.

    Args:
        stage (RetrievalStage): The retrieval stage to wrap.
            Must be properly configured for document retrieval.

    Example:
        >>> retrieval = RetrievalStage(...)
        >>> adapter = RetrievalStageAdapter(retrieval)
        >>> context = PipelineContext()
        >>> result = await adapter.process(
        ...     "What is machine learning?",
        ...     context
        ... )
        >>> assert isinstance(result, RetrievalResult)
        >>> assert len(result.chunks) > 0
    """

    def __init__(self, stage: RetrievalStage):
        """Initialize the adapter.

        Args:
            stage (RetrievalStage): The retrieval stage to wrap
        """
        super().__init__("retrieval")
        self._stage = stage

    async def process(self, data: str, context: PipelineContext) -> RetrievalResult:
        """Process data through the retrieval stage.

        Args:
            data (str): The query string to retrieve documents for
            context (PipelineContext): Pipeline execution context

        Returns:
            RetrievalResult: Contains:
                - chunks: List of retrieved and scored document chunks
                - query: Original query string
                - metadata: Additional retrieval information

        Raises:
            PepperPyError: If retrieval fails
        """
        chunks = await self._stage.process(data)
        scored_chunks = [ScoredChunk(chunk=chunk, score=1.0) for chunk in chunks]
        return RetrievalResult(chunks=scored_chunks, query=data)


class RerankingStageAdapter(PipelineStage[RetrievalResult, RerankingResult]):
    """Adapter for the reranking stage.

    This adapter wraps a RAG reranking stage to make it compatible with
    the new unified pipeline framework. It can also operate without a
    reranking stage, in which case it passes through the input chunks.

    Args:
        stage (Optional[RerankingStage]): The reranking stage to wrap,
            or None to use passthrough behavior.

    Example:
        >>> reranker = RerankingStage(...)
        >>> adapter = RerankingStageAdapter(reranker)
        >>> retrieval_result = RetrievalResult(...)
        >>> context = PipelineContext()
        >>> result = await adapter.process(retrieval_result, context)
        >>> assert isinstance(result, RerankingResult)
        >>> assert len(result.chunks) > 0
    """

    def __init__(self, stage: Optional[RerankingStage]):
        """Initialize the adapter.

        Args:
            stage (Optional[RerankingStage]): The reranking stage to wrap, or None
        """
        super().__init__("reranking")
        self._stage = stage

    async def process(
        self, data: RetrievalResult, context: PipelineContext
    ) -> RerankingResult:
        """Process data through the reranking stage.

        Args:
            data (RetrievalResult): The retrieval results to rerank
            context (PipelineContext): Pipeline execution context

        Returns:
            RerankingResult: Contains:
                - chunks: List of reranked document chunks
                - query: Original query string
                - original_chunks: Original chunks before reranking
                - metadata: Additional reranking information

        Raises:
            PepperPyError: If reranking fails
        """
        if self._stage:
            chunks = await self._stage.process(chunks=data.chunks, query=data.query)
            return RerankingResult(
                chunks=chunks,
                query=data.query,
                original_chunks=data.chunks,
            )
        else:
            # Create a simple reranking result if no stage is configured
            return RerankingResult(
                chunks=data.chunks,
                query=context.get("query", ""),
                original_chunks=data.chunks,
            )


class GenerationStageAdapter(PipelineStage[RerankingResult, GenerationResult]):
    """Adapter for the generation stage.

    This adapter wraps a RAG generation stage to make it compatible with
    the new unified pipeline framework. It ensures proper handling of
    context chunks and query information during generation.

    Args:
        stage (GenerationStage): The generation stage to wrap.
            Must be properly configured for text generation.

    Example:
        >>> generator = GenerationStage(...)
        >>> adapter = GenerationStageAdapter(generator)
        >>> reranking_result = RerankingResult(...)
        >>> context = PipelineContext()
        >>> result = await adapter.process(reranking_result, context)
        >>> assert isinstance(result, GenerationResult)
        >>> assert result.text != ""
    """

    def __init__(self, stage: GenerationStage):
        """Initialize the adapter.

        Args:
            stage (GenerationStage): The generation stage to wrap
        """
        super().__init__("generation")
        self._stage = stage

    async def process(
        self, data: RerankingResult, context: PipelineContext
    ) -> GenerationResult:
        """Process data through the generation stage.

        Args:
            data (RerankingResult): The reranking results to generate from
            context (PipelineContext): Pipeline execution context

        Returns:
            GenerationResult: Contains:
                - text: Generated response text
                - chunks: Context chunks used for generation
                - query: Original query string
                - metadata: Additional generation information

        Raises:
            PepperPyError: If generation fails
        """
        response = await self._stage.process(chunks=data.chunks, query=data.query)
        return GenerationResult(
            text=response.text,
            metadata=response.metadata,
            chunks=data.chunks,
            query=data.query,
        )


class RAGPipelineAdapter(NewPipeline[str, str]):
    """Adapter for the RAG pipeline.

    This adapter wraps a RAG pipeline to make it compatible with
    the new unified pipeline framework. It manages the flow of data
    through retrieval, optional reranking, and generation stages.

    Args:
        rag_pipeline (RAGPipeline): The RAG pipeline to wrap.
            Must have at least retrieval and generation stages configured.
        name (str): Name for the new pipeline.
            Used for identification and logging.

    Raises:
        ValueError: If required stages are missing from the pipeline.

    Example:
        >>> from pepperpy.rag.pipeline import RAGPipeline
        >>> from pepperpy.rag.stages import RetrievalStage, GenerationStage
        >>>
        >>> # Create a RAG pipeline
        >>> rag = RAGPipeline(
        ...     retrieval_stage=RetrievalStage(...),
        ...     generation_stage=GenerationStage(...)
        ... )
        >>>
        >>> # Wrap it in the adapter
        >>> pipeline = RAGPipelineAdapter(rag, "rag_pipeline")
        >>>
        >>> # Use it with the new interface
        >>> context = PipelineContext()
        >>> result = await pipeline.execute(
        ...     "What is the meaning of life?",
        ...     context
        ... )
        >>> print(result)  # Generated response
    """

    def __init__(self, rag_pipeline: RAGPipeline, name: str):
        """Initialize the adapter.

        Args:
            rag_pipeline (RAGPipeline): The RAG pipeline to wrap
            name (str): Name for the new pipeline

        Raises:
            ValueError: If required stages are missing
        """
        super().__init__(name)
        self._rag = rag_pipeline

        # Add the stage adapters
        if not rag_pipeline.retrieval_stage:
            raise ValueError("RAG pipeline must have a retrieval stage")
        self.add_stage(RetrievalStageAdapter(rag_pipeline.retrieval_stage))

        if rag_pipeline.reranking_stage:
            self.add_stage(RerankingStageAdapter(rag_pipeline.reranking_stage))

        if not rag_pipeline.generation_stage:
            raise ValueError("RAG pipeline must have a generation stage")
        self.add_stage(GenerationStageAdapter(rag_pipeline.generation_stage))

    async def execute(
        self, query: str, context: Optional[PipelineContext] = None
    ) -> str:
        """Execute the RAG pipeline.

        Args:
            query (str): The query string to process
            context (Optional[PipelineContext]): Pipeline execution context.
                If None, a new context will be created.

        Returns:
            str: The generated response text

        Raises:
            PepperPyError: If pipeline execution fails
        """
        # Create context if not provided
        if context is None:
            context = PipelineContext()

        # Store the query in context for reranking
        context.set("query", query)

        # Execute the pipeline stages
        result = await super().execute(query, context)

        # Extract text from response
        if isinstance(result, GenerationResult):
            return result.text
        return str(result)

    def get_config_dict(self) -> Dict[str, Any]:
        """Get the pipeline configuration as a dictionary.

        Returns:
            Dict[str, Any]: Contains:
                - name: Pipeline name
                - type: Adapter type identifier
                - config: Underlying RAG pipeline configuration
        """
        return {
            "name": self.name,
            "type": "rag_adapter",
            "config": self._rag.config.__dict__ if self._rag.config else {},
        }


class RAGPipelineBuilderAdapter:
    """Builder for creating RAG pipelines using the new framework.

    This adapter provides factory methods for creating RAG pipelines
    that are compatible with the new unified pipeline framework.
    It supports creating different pipeline configurations optimized
    for various use cases.

    Example:
        >>> builder = RAGPipelineBuilderAdapter()
        >>> pipeline = await builder.create_simple_pipeline(
        ...     retrieval_stage=RetrievalStage(...),
        ...     generation_stage=GenerationStage(...),
        ...     name="my_simple_rag"
        ... )
        >>>
        >>> context = PipelineContext()
        >>> result = await pipeline.execute(
        ...     "What are the key features of Python?",
        ...     context
        ... )
        >>> print(result)  # Generated response
    """

    async def create_simple_pipeline(
        self,
        retrieval_stage: RetrievalStage,
        generation_stage: GenerationStage,
        name: str = "simple_rag",
    ) -> RAGPipelineAdapter:
        """Create a simple RAG pipeline.

        Creates a basic pipeline with just retrieval and generation stages,
        suitable for straightforward question-answering tasks.

        Args:
            retrieval_stage (RetrievalStage): The retrieval stage
            generation_stage (GenerationStage): The generation stage
            name (str, optional): Name for the pipeline. Defaults to "simple_rag"

        Returns:
            RAGPipelineAdapter: The created pipeline adapter

        Example:
            >>> pipeline = await builder.create_simple_pipeline(
            ...     retrieval_stage=retriever,
            ...     generation_stage=generator,
            ...     name="qa_pipeline"
            ... )
        """
        rag = RAGPipeline(name)
        rag.set_retrieval_stage(retrieval_stage)
        rag.set_generation_stage(generation_stage)
        return RAGPipelineAdapter(rag, name)

    async def create_default_pipeline(
        self,
        retrieval_stage: RetrievalStage,
        reranking_stage: RerankingStage,
        generation_stage: GenerationStage,
        name: str = "default_rag",
    ) -> RAGPipelineAdapter:
        """Create a default RAG pipeline.

        Creates a full-featured pipeline with retrieval, reranking, and
        generation stages, suitable for high-quality response generation.

        Args:
            retrieval_stage (RetrievalStage): The retrieval stage
            reranking_stage (RerankingStage): The reranking stage
            generation_stage (GenerationStage): The generation stage
            name (str, optional): Name for the pipeline. Defaults to "default_rag"

        Returns:
            RAGPipelineAdapter: The created pipeline adapter

        Example:
            >>> pipeline = await builder.create_default_pipeline(
            ...     retrieval_stage=retriever,
            ...     reranking_stage=reranker,
            ...     generation_stage=generator,
            ...     name="full_pipeline"
            ... )
        """
        rag = RAGPipeline(name)
        rag.set_retrieval_stage(retrieval_stage)
        rag.set_reranking_stage(reranking_stage)
        rag.set_generation_stage(generation_stage)
        return RAGPipelineAdapter(rag, name)

    async def create_metadata_focused_pipeline(
        self,
        retrieval_stage: RetrievalStage,
        generation_stage: GenerationStage,
        name: str = "metadata_rag",
    ) -> RAGPipelineAdapter:
        """Create a metadata-focused RAG pipeline.

        Creates a pipeline optimized for metadata-aware retrieval and generation,
        suitable for tasks requiring strong metadata filtering and ranking.

        Args:
            retrieval_stage (RetrievalStage): The retrieval stage
            generation_stage (GenerationStage): The generation stage
            name (str, optional): Name for the pipeline. Defaults to "metadata_rag"

        Returns:
            RAGPipelineAdapter: The created pipeline adapter

        Example:
            >>> pipeline = await builder.create_metadata_focused_pipeline(
            ...     retrieval_stage=retriever,
            ...     generation_stage=generator,
            ...     name="metadata_pipeline"
            ... )
        """
        # Configure the retrieval stage to focus on metadata
        if hasattr(retrieval_stage, "config") and hasattr(
            retrieval_stage.config, "metadata_filters"
        ):
            retrieval_stage.config.metadata_filters = {"weight": 0.7}

        rag = RAGPipeline(name)
        rag.set_retrieval_stage(retrieval_stage)
        rag.set_generation_stage(generation_stage)
        return RAGPipelineAdapter(rag, name)
