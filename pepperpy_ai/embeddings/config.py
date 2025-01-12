"""Embeddings configuration."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbeddingsConfig:
    """Configuration for embeddings capability."""

    # Required fields
    model_name: str
    dimension: int
    batch_size: int

    # Optional fields with defaults
    name: str = "embeddings"
    version: str = "1.0.0"
    enabled: bool = True
    device: str = "cpu"
    normalize_embeddings: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.dimension <= 0:
            raise ValueError("Dimension must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
