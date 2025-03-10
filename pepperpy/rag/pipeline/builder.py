"""Pipeline builder for RAG system.

This module provides functionality for building and configuring RAG pipelines.
"""

from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.rag.errors import PipelineError
from pepperpy.rag.pipeline.stages.generation import (
    GenerationProvider,
    GenerationStage,
    GenerationStageConfig,
)
from pepperpy.rag.pipeline.stages.reranking import (
    RerankerProvider,
    RerankingStage,
    RerankingStageConfig,
)
from pepperpy.rag.pipeline.stages.retrieval import (
    EmbeddingProvider,
    RetrievalStage,
    RetrievalStageConfig,
)
from pepperpy.rag.storage.core import VectorStore
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for stage configurations
T = TypeVar("T")


class PipelineStage(Protocol):
    """Protocol for pipeline stages."""

    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a query with optional context.

        Args:
            query: The query to process
            context: Optional context from previous stages

        Returns:
            Dictionary containing stage outputs
        """
        ...


class RAGPipeline:
    """RAG pipeline for processing queries through multiple stages."""

    def __init__(self, stages: List[PipelineStage]):
        """Initialize RAG pipeline.

        Args:
            stages: List of pipeline stages to execute in order
        """
        self.stages = stages

    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a query through all pipeline stages.

        Args:
            query: The query to process
            context: Optional initial context

        Returns:
            Dictionary containing outputs from all stages

        Raises:
            PipelineError: If there is an error during pipeline execution
        """
        try:
            current_context = context or {}

            for stage in self.stages:
                current_context = await stage.process(
                    query=query,
                    context=current_context,
                )

            return current_context

        except Exception as e:
            raise PipelineError(f"Error in pipeline execution: {e}")


class RAGPipelineBuilder:
    """Builder for constructing RAG pipelines.

    This builder helps users configure and construct RAG pipelines with
    the desired stages and configurations.
    """

    def __init__(self):
        """Initialize pipeline builder."""
        self.stages: List[PipelineStage] = []
        self._retrieval_stage: Optional[RetrievalStage] = None
        self._reranking_stage: Optional[RerankingStage] = None
        self._generation_stage: Optional[GenerationStage] = None

    def with_retrieval(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        config: Optional[RetrievalStageConfig] = None,
    ) -> "RAGPipelineBuilder":
        """Add retrieval stage to pipeline.

        Args:
            vector_store: Vector store for document retrieval
            embedding_provider: Provider for generating embeddings
            config: Optional stage configuration

        Returns:
            Self for method chaining
        """
        self._retrieval_stage = RetrievalStage(
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            config=config,
        )
        return self

    def with_reranking(
        self,
        reranker: RerankerProvider,
        config: Optional[RerankingStageConfig] = None,
    ) -> "RAGPipelineBuilder":
        """Add reranking stage to pipeline.

        Args:
            reranker: Provider for reranking documents
            config: Optional stage configuration

        Returns:
            Self for method chaining
        """
        self._reranking_stage = RerankingStage(
            reranker=reranker,
            config=config,
        )
        return self

    def with_generation(
        self,
        generator: GenerationProvider,
        config: Optional[GenerationStageConfig] = None,
    ) -> "RAGPipelineBuilder":
        """Add generation stage to pipeline.

        Args:
            generator: Provider for generating responses
            config: Optional stage configuration

        Returns:
            Self for method chaining
        """
        self._generation_stage = GenerationStage(
            generator=generator,
            config=config,
        )
        return self

    def build(self) -> RAGPipeline:
        """Build the configured pipeline.

        Returns:
            Configured RAG pipeline

        Raises:
            PipelineError: If pipeline configuration is invalid
        """
        if not self._retrieval_stage:
            raise PipelineError("Retrieval stage is required")

        if not self._generation_stage:
            raise PipelineError("Generation stage is required")

        # Build stages list in order
        stages = [self._retrieval_stage]

        if self._reranking_stage:
            stages.append(self._reranking_stage)

        stages.append(self._generation_stage)

        return RAGPipeline(stages=stages)
