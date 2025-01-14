"""LLM configuration."""

from typing import Any, NotRequired, TypedDict


class LLMConfig(TypedDict, total=False):
    """LLM configuration."""

    # Required fields
    name: str
    version: str

    # Optional fields
    enabled: NotRequired[bool]
    metadata: NotRequired[dict[str, Any]]
    settings: NotRequired[dict[str, Any]]
    api_key: NotRequired[str]
    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization_id: NotRequired[str]
    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
    stop_sequences: NotRequired[list[str]]
