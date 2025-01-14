"""Capabilities module exports."""

from typing import TypedDict

from .base import BaseCapability
from .embeddings.base import BaseEmbeddingsCapability
from .rag.base import BaseRAGStrategy


class CapabilityConfig(TypedDict, total=False):
    """Base capability configuration."""

    model: str | None
    temperature: float | None
    max_tokens: int | None
    top_p: float | None
    frequency_penalty: float | None
    presence_penalty: float | None
    timeout: float | None


__all__ = [
    "BaseCapability",
    "BaseEmbeddingsCapability",
    "BaseRAGStrategy",
    "CapabilityConfig",
]
