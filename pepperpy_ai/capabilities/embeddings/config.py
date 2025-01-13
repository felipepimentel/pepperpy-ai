"""Embeddings configuration module."""

from dataclasses import dataclass

from ..config import CapabilityConfig


@dataclass
class EmbeddingsConfig(CapabilityConfig):
    """Embeddings capability configuration."""

    dimensions: int | None = None
    batch_size: int | None = None
    normalize: bool = True
    pooling_strategy: str = "mean"
    device: str | None = None 