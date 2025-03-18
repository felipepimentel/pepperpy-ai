"""Core RAG pipeline implementation using the unified pipeline framework.

This module provides the core RAG pipeline implementation that orchestrates
the retrieval, reranking, and generation stages in a configurable way.
"""

from typing import Any, Dict, Optional, cast

from pepperpy.core.pipeline.base import (
    Pipeline,
    PipelineConfig,
    PipelineContext,
    PipelineStage,
)
from pepperpy.rag.models import (
    GenerationResult,
)
from pepperpy.rag.pipeline.stages import (
    GenerationStage,
    RerankingStage,
    RetrievalStage,
)


class RAGPipeline(Pipeline[str, GenerationResult]):
    """A Retrieval-Augmented Generation (RAG) pipeline.

    This pipeline orchestrates the RAG process through three main stages:
    1. Retrieval: Finding relevant documents from a knowledge base
    2. Reranking: Optionally reranking retrieved documents by relevance
    3. Generation: Generating a response using the retrieved context

    Example:
        >>> from pepperpy.rag.pipeline import RAGPipelineBuilder
        >>> pipeline = RAGPipelineBuilder.create_default_pipeline()
        >>> context = PipelineContext()
        >>> result = await pipeline.execute("What is RAG?", context)
        >>> assert isinstance(result, GenerationResult)
    """

    def __init__(
        self,
        name: str,
        config: Optional[PipelineConfig] = None,
    ) -> None:
        """Initialize a RAG pipeline.

        Args:
            name: The name of the pipeline
            config: Optional pipeline configuration
        """
        super().__init__(name, config=config)
        self._retrieval_stage: Optional[RetrievalStage] = None
        self._reranking_stage: Optional[RerankingStage] = None
        self._generation_stage: Optional[GenerationStage] = None

    @property
    def retrieval_stage(self) -> Optional[RetrievalStage]:
        """Get the retrieval stage."""
        return self._retrieval_stage

    @property
    def reranking_stage(self) -> Optional[RerankingStage]:
        """Get the reranking stage."""
        return self._reranking_stage

    @property
    def generation_stage(self) -> Optional[GenerationStage]:
        """Get the generation stage."""
        return self._generation_stage

    def set_retrieval_stage(self, stage: RetrievalStage) -> None:
        """Set the retrieval stage.

        Args:
            stage: The retrieval stage to use
        """
        if self._retrieval_stage is not None:
            self._stages.remove(
                cast(PipelineStage[str, GenerationResult], self._retrieval_stage)
            )
        self._retrieval_stage = stage
        self.add_stage(cast(PipelineStage[str, GenerationResult], stage))

    def set_reranking_stage(self, stage: RerankingStage) -> None:
        """Set the reranking stage.

        Args:
            stage: The reranking stage to use
        """
        if self._reranking_stage is not None:
            self._stages.remove(
                cast(PipelineStage[str, GenerationResult], self._reranking_stage)
            )
        self._reranking_stage = stage
        self.add_stage(cast(PipelineStage[str, GenerationResult], stage))

    def set_generation_stage(self, stage: GenerationStage) -> None:
        """Set the generation stage.

        Args:
            stage: The generation stage to use
        """
        if self._generation_stage is not None:
            self._stages.remove(
                cast(PipelineStage[str, GenerationResult], self._generation_stage)
            )
        self._generation_stage = stage
        self.add_stage(cast(PipelineStage[str, GenerationResult], stage))

    async def execute(
        self,
        query: str,
        context: Optional[PipelineContext] = None,
    ) -> GenerationResult:
        """Execute the RAG pipeline on a query.

        Args:
            query: The query to process
            context: Optional pipeline context

        Returns:
            The generation result containing the response and metadata

        Raises:
            ValueError: If required stages are missing
        """
        if self._retrieval_stage is None:
            raise ValueError("Retrieval stage is required but not set")
        if self._generation_stage is None:
            raise ValueError("Generation stage is required but not set")

        if context is None:
            context = PipelineContext()

        # Store query in context
        context.set("query", query)

        # Execute pipeline stages
        result = await super().execute(query, context)

        # Return final generation result
        return result

    def get_config_dict(self) -> Dict[str, Any]:
        """Get the pipeline configuration as a dictionary.

        Returns:
            A dictionary containing the pipeline configuration and stages
        """
        return {
            "name": self.name,
            "config": {
                "name": self.config.name,
                "description": self.config.description,
                "metadata": self.config.metadata,
                "options": self.config.options,
            }
            if self.config
            else None,
            "stages": [
                {
                    "type": stage.__class__.__name__.lower().replace("stage", ""),
                    "name": stage.name,
                    "description": stage.description,
                }
                for stage in self.stages
            ],
        }

    @classmethod
    def create_from_config(cls, config_dict: Dict[str, Any]) -> "RAGPipeline":
        """Create a pipeline from a configuration dictionary.

        Args:
            config_dict: The configuration dictionary

        Returns:
            A new RAGPipeline instance
        """
        config = (
            PipelineConfig(**config_dict["config"])
            if config_dict.get("config")
            else None
        )
        pipeline = cls(config_dict["name"], config)

        for stage_data in config_dict["stages"]:
            stage = pipeline._create_stage_from_config(stage_data)
            if isinstance(stage, RetrievalStage):
                pipeline.set_retrieval_stage(stage)
            elif isinstance(stage, RerankingStage):
                pipeline.set_reranking_stage(stage)
            elif isinstance(stage, GenerationStage):
                pipeline.set_generation_stage(stage)

        return pipeline

    def _create_stage_from_config(self, config: Dict[str, Any]) -> Any:
        """Create a pipeline stage from a configuration dictionary.

        Args:
            config: The stage configuration dictionary

        Returns:
            A new pipeline stage instance

        Raises:
            ValueError: If the stage type is unknown
        """
        stage_type = config.get("type")
        stage_config = {
            "name": config["name"],
            "description": config.get("description", ""),
        }

        if stage_type == "retrieval":
            return RetrievalStage(**stage_config)
        elif stage_type == "reranking":
            return RerankingStage(**stage_config)
        elif stage_type == "generation":
            return GenerationStage(**stage_config)
        else:
            raise ValueError(f"Unknown stage type: {stage_type}")
