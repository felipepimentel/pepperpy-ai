"""Pipeline module for RAG.

This module provides the RAG pipeline functionality, which orchestrates
the retrieval, reranking, and generation stages of the RAG process.
"""

from pepperpy.rag.pipeline.builder import (
    RAGPipelineBuilder,
)
from pepperpy.rag.pipeline.core import (
    AbstractPipeline,
    PipelineConfig,
    PipelineStage,
    RAGPipeline,
    create_default_pipeline,
    create_metadata_focused_pipeline,
    create_simple_pipeline,
    process_document,
    process_documents,
)
from pepperpy.rag.pipeline.stages import (
    GenerationStage,
    RerankingStage,
    RetrievalStage,
)

__all__ = [
    # Core pipeline classes
    "RAGPipeline",
    "PipelineConfig",
    "PipelineStage",
    "AbstractPipeline",
    # Builder
    "RAGPipelineBuilder",
    # Factory functions
    "create_default_pipeline",
    "create_simple_pipeline",
    "create_metadata_focused_pipeline",
    # Processing functions
    "process_document",
    "process_documents",
    # Pipeline stages
    "RetrievalStage",
    "RerankingStage",
    "GenerationStage",
]
