"""Embeddings base module."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..config.base import BaseConfig
from ..types import JsonDict

@dataclass
class EmbeddingsConfig(BaseConfig):
    """Embeddings configuration class."""

    name: str = "embeddings"
    version: str = "1.0.0"
    enabled: bool = True
    model_name: str = "default"
    dimension: int = 768
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        super().__post_init__()

        if not self.model_name:
            raise ValueError("Model name cannot be empty")

        if not isinstance(self.dimension, int):
            raise ValueError("Dimension must be an integer")

        if not isinstance(self.device, str):
            raise ValueError("Device must be a string")

        if not isinstance(self.normalize_embeddings, bool):
            raise ValueError("Normalize embeddings must be a boolean")

        if not isinstance(self.batch_size, int):
            raise ValueError("Batch size must be an integer")
