"""Embeddings configuration module."""

from dataclasses import dataclass

from pepperpy_core.types import BaseConfig


@dataclass
class EmbeddingsConfig(BaseConfig):
    """Embeddings capability configuration."""

    name: str
    version: str
    model: str | None = None
    dimensions: int | None = None
    batch_size: int | None = None
    normalize: bool = True
    pooling_strategy: str = "mean"
    device: str | None = None
