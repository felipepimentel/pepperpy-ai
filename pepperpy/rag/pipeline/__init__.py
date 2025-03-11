"""
PepperPy RAG Pipeline Module.

Este módulo contém os componentes para construir pipelines RAG.
"""

from __future__ import annotations

from pepperpy.rag.pipeline.builder import RAGPipeline, RAGPipelineBuilder
from pepperpy.rag.pipeline.core import (
    Pipeline,
    PipelineConfig,
    PipelineInput,
    PipelineOutput,
    PipelineStep,
)
from pepperpy.rag.pipeline.stages import (
    EmbeddingProvider,
    GenerationProvider,
    GenerationResult,
    GenerationStage,
    GenerationStageConfig,
    PipelineStage,
    RerankerProvider,
    RerankingResult,
    RerankingStage,
    RerankingStageConfig,
    RetrievalResult,
    RetrievalStage,
    RetrievalStageConfig,
    StageConfig,
)

__all__ = [
    # Core
    "Pipeline",
    "PipelineConfig",
    "PipelineInput",
    "PipelineOutput",
    "PipelineStep",
    "RAGPipeline",
    "RAGPipelineBuilder",
    # Stages
    "PipelineStage",
    "StageConfig",
    # Retrieval
    "RetrievalStage",
    "RetrievalStageConfig",
    "RetrievalResult",
    "EmbeddingProvider",
    # Reranking
    "RerankingStage",
    "RerankingStageConfig",
    "RerankingResult",
    "RerankerProvider",
    # Generation
    "GenerationStage",
    "GenerationStageConfig",
    "GenerationResult",
    "GenerationProvider",
]
