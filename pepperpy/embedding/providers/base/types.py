"""Type definitions for embedding providers.

This module defines the types used by embedding providers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Union

import numpy as np

# Type alias for embedding vectors
Embedding = np.ndarray


class EmbeddingProvider(Protocol):
    """Protocol defining the interface for embedding providers."""

    def embed(
        self,
        text: Union[str, List[str]],
        **kwargs,
    ) -> Union["Embedding", List["Embedding"]]:
        """Generate embeddings for text."""
        ...

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        ...

    def get_models(self) -> List[str]:
        """Get list of available embedding models."""
        ...


@dataclass
class ModelParameters:
    """Parameters for embedding models."""

    model: str
    dimensions: int
    max_input_length: int
    context_window: int
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Response from embedding provider."""

    embeddings: Union["Embedding", List["Embedding"]]
    model: str
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
