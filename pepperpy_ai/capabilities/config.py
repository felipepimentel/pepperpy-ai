"""Capability configuration types."""

from typing import NotRequired, TypedDict


class CapabilityConfig(TypedDict, total=False):
    """Base capability configuration."""

    api_key: NotRequired[str]
    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
