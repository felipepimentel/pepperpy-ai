"""LLM configuration module."""

from typing import NotRequired, TypedDict


class LLMConfig(TypedDict, total=False):
    """LLM configuration."""

    provider: str
    name: str
    version: str
    model: str
    api_key: str
    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
