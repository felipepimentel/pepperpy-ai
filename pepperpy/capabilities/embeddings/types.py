"""Embeddings types module."""

from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Embedding result."""

    embeddings: list[float]
    metadata: dict[str, str | int | float | None]
