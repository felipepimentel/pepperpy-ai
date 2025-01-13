"""Provider configuration module."""

from typing import NotRequired, TypedDict


class ProviderConfig(TypedDict, total=False):
    """Provider configuration dictionary."""

    api_key: NotRequired[str]
    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
