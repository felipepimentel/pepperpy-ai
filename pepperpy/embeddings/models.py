"""Models for the embeddings module.

This module defines the data models used by the embeddings providers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EmbeddingOptions:
    """Options for embedding generation.

    Attributes:
        model: Model to use for embedding generation
        dimensions: Number of dimensions for the embeddings
        normalize: Whether to normalize the embeddings
        additional_options: Additional provider-specific options
    """

    model: str = "default"
    dimensions: Optional[int] = None
    normalize: bool = False
    additional_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation.

    Attributes:
        embedding: The generated embedding vector
        usage: Token usage information
        metadata: Additional metadata about the embedding
    """

    embedding: List[float]
    usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict) 