"""RAG configuration."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RAGStrategyConfig:
    """RAG strategy configuration."""

    model_name: str
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    metadata: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
