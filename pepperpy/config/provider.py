"""Provider configuration module."""

from typing import NotRequired, TypedDict


class ProviderConfig(TypedDict, total=True):
    """Provider configuration."""

    name: str
    version: str
    model: str
    api_key: str
    api_base: str
    organization_id: NotRequired[str | None]
    api_version: NotRequired[str | None]
    organization: NotRequired[str | None]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
    max_retries: NotRequired[int]
    enabled: NotRequired[bool]
