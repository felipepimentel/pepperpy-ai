"""Pipeline builder for the RAG system."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pepperpy.errors import PepperpyError
from pepperpy.llm.utils import Response
from pepperpy.rag.pipeline.stages.generation import (
    GenerationStage,
    GenerationStageConfig,
)
from pepperpy.rag.pipeline.stages.reranking import (
    RerankingStage,
    RerankingStageConfig,
)
from pepperpy.rag.pipeline.stages.retrieval import (
    RetrievalStage,
    RetrievalStageConfig,
)


@dataclass
class RAGPipelineConfig:
    """Configuration for the RAG pipeline."""

    retrieval: RetrievalStageConfig
    reranking: Optional[RerankingStageConfig] = None
    generation: Optional[GenerationStageConfig] = None


class RAGPipeline:
    """Pipeline for RAG processing."""

    def __init__(self, config: RAGPipelineConfig):
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.retrieval_stage = RetrievalStage(config.retrieval)
        self.reranking_stage = (
            RerankingStage(config.reranking) if config.reranking else None
        )
        self.generation_stage = (
            GenerationStage(config.generation) if config.generation else None
        )

    async def process(
        self,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Process a query through the pipeline.

        Args:
            query: User query
            metadata: Optional metadata

        Returns:
            Generated response

        Raises:
            PepperpyError: If processing fails
        """
        try:
            # Retrieve relevant chunks
            chunks = await self.retrieval_stage.process(query, metadata)

            # Rerank chunks if configured
            if self.reranking_stage:
                chunks = await self.reranking_stage.process(query, chunks, metadata)

            # Generate response if configured
            if self.generation_stage:
                return await self.generation_stage.process(query, chunks, metadata)

            # Return empty response if no generation stage
            return Response(
                text="",
                usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0},
                metadata=metadata or {},
            )

        except Exception as e:
            raise PepperpyError(f"Error in RAG pipeline: {e}")


class RAGPipelineBuilder:
    """Builder for RAG pipelines."""

    def __init__(self):
        """Initialize the builder."""
        self.retrieval_config: Optional[RetrievalStageConfig] = None
        self.reranking_config: Optional[RerankingStageConfig] = None
        self.generation_config: Optional[GenerationStageConfig] = None

    def with_retrieval(self, config: RetrievalStageConfig) -> "RAGPipelineBuilder":
        """Add retrieval stage.

        Args:
            config: Stage configuration

        Returns:
            Self for chaining
        """
        self.retrieval_config = config
        return self

    def with_reranking(self, config: RerankingStageConfig) -> "RAGPipelineBuilder":
        """Add reranking stage.

        Args:
            config: Stage configuration

        Returns:
            Self for chaining
        """
        self.reranking_config = config
        return self

    def with_generation(self, config: GenerationStageConfig) -> "RAGPipelineBuilder":
        """Add generation stage.

        Args:
            config: Stage configuration

        Returns:
            Self for chaining
        """
        self.generation_config = config
        return self

    def build(self) -> RAGPipeline:
        """Build the pipeline.

        Returns:
            Configured pipeline

        Raises:
            PepperpyError: If configuration is invalid
        """
        if not self.retrieval_config:
            raise PepperpyError("Retrieval stage is required")

        config = RAGPipelineConfig(
            retrieval=self.retrieval_config,
            reranking=self.reranking_config,
            generation=self.generation_config,
        )

        return RAGPipeline(config)


# Export all classes
__all__ = [
    "RAGPipelineConfig",
    "RAGPipeline",
    "RAGPipelineBuilder",
]
