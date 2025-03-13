"""RAG Pipeline stages.

This module provides the stages used in the RAG pipeline,
including retrieval, reranking, and generation stages.
"""

from pepperpy.rag.interfaces import (
    EmbeddingProvider,
    GenerationProvider,
    PipelineStage,
    RerankerProvider,
)
from pepperpy.rag.models import (
    GenerationResult,
    RerankingResult,
    RetrievalResult,
)
from pepperpy.rag.pipeline.stages.base import StageConfig
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

__all__ = [
    # Base classes
    "PipelineStage",
    "StageConfig",
    # Retrieval stage
    "RetrievalStage",
    "RetrievalStageConfig",
    "RetrievalResult",
    "EmbeddingProvider",
    # Reranking stage
    "RerankingStage",
    "RerankingStageConfig",
    "RerankingResult",
    "RerankerProvider",
    # Generation stage
    "GenerationStage",
    "GenerationStageConfig",
    "GenerationResult",
    "GenerationProvider",
]
