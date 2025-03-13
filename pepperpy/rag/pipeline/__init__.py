"""RAG Pipeline system.

This module provides the RAG pipeline system that orchestrates document processing
through multiple stages including transformation, metadata extraction, chunking,
retrieval, reranking, and generation.
"""

from __future__ import annotations

from pepperpy.rag.pipeline.core import (
    AbstractPipeline,
    AbstractPipelineStage,
    PipelineConfig,
    PipelineStage,
    RAGPipeline,
    RAGPipelineBuilder,
    create_default_pipeline,
    create_metadata_focused_pipeline,
    create_simple_pipeline,
    process_document,
    process_documents,
)

__all__ = [
    # Base classes
    "AbstractPipeline",
    "AbstractPipelineStage",
    "PipelineConfig",
    "PipelineStage",
    # Pipeline implementation
    "RAGPipeline",
    "RAGPipelineBuilder",
    # Helper functions
    "create_default_pipeline",
    "create_metadata_focused_pipeline",
    "create_simple_pipeline",
    "process_document",
    "process_documents",
]
