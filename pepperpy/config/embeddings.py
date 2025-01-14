"""Embeddings configuration module."""

from typing import NotRequired, TypedDict


class EmbeddingsConfig(TypedDict, total=True):
    """Embeddings configuration."""

    name: str
    version: str
    model: str
    api_key: str
    provider_type: NotRequired[str]
    enabled: NotRequired[bool]
    normalize: NotRequired[bool]
    batch_size: NotRequired[int]
    device: NotRequired[str]
    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
