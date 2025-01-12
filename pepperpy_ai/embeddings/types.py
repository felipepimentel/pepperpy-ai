"""Embedding types module."""

from dataclasses import dataclass
from typing import Any

# Type alias for embedding vectors
EmbeddingVector = list[float]


@dataclass
class EmbeddingResult:
    """Result of embedding operation."""

    embeddings: EmbeddingVector
    metadata: dict[str, Any] | None = None

    def __len__(self) -> int:
        """Get length of embeddings."""
        return len(self.embeddings)
