"""Pipeline stages for the RAG system."""

from pepperpy.rag.pipeline.core import PipelineConfig as StageConfig
from pepperpy.rag.pipeline.core import PipelineStage
from pepperpy.rag.pipeline.stages.generation import (
    GenerationProvider,
    GenerationResult,
    GenerationStage,
    GenerationStageConfig,
)
from pepperpy.rag.pipeline.stages.reranking import (
    RerankerProvider,
    RerankingResult,
    RerankingStage,
    RerankingStageConfig,
)
from pepperpy.rag.pipeline.stages.retrieval import (
    EmbeddingProvider,
    RetrievalResult,
    RetrievalStage,
    RetrievalStageConfig,
)

__all__ = [
    # Core
    "PipelineStage",
    "StageConfig",
    # Generation
    "GenerationProvider",
    "GenerationStage",
    "GenerationStageConfig",
    "GenerationResult",
    # Retrieval
    "EmbeddingProvider",
    "RetrievalStage",
    "RetrievalStageConfig",
    "RetrievalResult",
    # Reranking
    "RerankerProvider",
    "RerankingStage",
    "RerankingStageConfig",
    "RerankingResult",
]
