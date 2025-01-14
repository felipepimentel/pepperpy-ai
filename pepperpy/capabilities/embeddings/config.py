"""Embeddings capability configuration."""

from typing import Any, NotRequired

from ..config import CapabilityConfig


class EmbeddingsConfig(CapabilityConfig, total=False):
    """Embeddings capability configuration."""

    # Required fields
    model_name: str
    dimension: int
    batch_size: int

    # Optional fields
    name: NotRequired[str]
    version: NotRequired[str]
    enabled: NotRequired[bool]
    device: NotRequired[str]
    normalize_embeddings: NotRequired[bool]
    metadata: NotRequired[dict[str, Any]]
    settings: NotRequired[dict[str, Any]]
    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization_id: NotRequired[str]
