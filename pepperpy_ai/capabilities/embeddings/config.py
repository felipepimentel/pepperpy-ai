"""Embeddings capability configuration."""

from typing import NotRequired

from ..config import CapabilityConfig


class EmbeddingsConfig(CapabilityConfig):
    """Embeddings capability configuration."""

    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization_id: NotRequired[str]
    batch_size: NotRequired[int]
