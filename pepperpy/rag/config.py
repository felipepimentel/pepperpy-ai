"""Configuration for the RAG system.

This module provides configuration classes for the RAG system.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RagConfig(BaseModel):
    """Configuration for a RAG pipeline."""

    id: str
    name: str
    description: str = ""

    # Component configurations
    indexers: List[Dict[str, Any]] = Field(default_factory=list)
    retrievers: List[Dict[str, Any]] = Field(default_factory=list)
    generators: List[Dict[str, Any]] = Field(default_factory=list)

    # Default components
    default_retriever: Optional[str] = None
    default_generator: Optional[str] = None

    # Additional configuration
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkingConfig(BaseModel):
    """Configuration for chunking."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunk_strategy: str = "recursive"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingConfig(BaseModel):
    """Configuration for embedding."""

    model_name: str
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    batch_size: int = 32
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexConfig(BaseModel):
    """Configuration for indexing."""

    index_type: str
    index_name: str
    index_path: Optional[str] = None
    similarity_metric: str = "cosine"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalConfig(BaseModel):
    """Configuration for retrieval."""

    retriever_type: str
    top_k: int = 5
    similarity_threshold: float = 0.7
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationConfig(BaseModel):
    """Configuration for generation."""

    generator_type: str
    model_name: str
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def create_default_config(
    pipeline_id: str,
    pipeline_name: str,
    description: str = "Default RAG pipeline",
) -> RagConfig:
    """Create a default RAG configuration.

    Args:
        pipeline_id: Unique identifier for the pipeline
        pipeline_name: Human-readable name for the pipeline
        description: Description of the pipeline

    Returns:
        A default RAG configuration

    """
    return RagConfig(
        id=pipeline_id,
        name=pipeline_name,
        description=description,
        indexers=[],
        retrievers=[],
        generators=[],
    )
