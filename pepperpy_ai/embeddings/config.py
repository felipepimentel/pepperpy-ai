"""Embeddings configuration module."""

from typing import NotRequired, TypedDict


class EmbeddingsConfig(TypedDict, total=False):
    """Embeddings configuration."""

    name: str
    version: str
    model: str
    enabled: NotRequired[bool]
    normalize: NotRequired[bool]
    batch_size: NotRequired[int]
    api_key: NotRequired[str]
    device: NotRequired[str]
