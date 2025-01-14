"""Embeddings types module."""

from dataclasses import dataclass
from typing import Any

# Type alias for embedding vectors
type EmbeddingVector = list[float]
"""Type alias for embedding vectors."""

type EmbeddingResult = list[float]
"""Type alias for embedding result."""

type BatchEmbeddingResult = list[list[float]]
"""Type alias for batch embedding result."""


@dataclass
class EmbeddingMetadata:
    """Result of embedding operation."""

    model: str
    """The model used for embedding."""

    dimensions: int
    """The dimensions of the embedding."""

    metadata: dict[str, Any]
    """Additional metadata about the embedding."""
