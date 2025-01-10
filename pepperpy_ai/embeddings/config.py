"""Embedding configuration."""

from dataclasses import dataclass, field

from ..config.base import BaseConfigData, JsonDict


@dataclass
class EmbeddingConfig(BaseConfigData):
    """Embedding configuration."""

    # Required fields first (no defaults)
    name: str
    model_name: str
    dimension: int
    batch_size: int

    # Optional fields (with defaults)
    device: str = "cpu"
    normalize_embeddings: bool = True
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
