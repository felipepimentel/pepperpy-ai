"""Provider configuration module."""

from dataclasses import dataclass, field
from typing import TypedDict

from ..types import JsonDict


class ProviderSettings(TypedDict, total=False):
    """Provider settings."""

    timeout: float
    max_retries: int
    retry_delay: float
    api_key: str
    api_base: str
    model: str
    metadata: JsonDict


@dataclass
class ProviderConfig:
    """Base provider configuration."""

    name: str
    version: str
    model: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    metadata: JsonDict = field(default_factory=dict)
    settings: ProviderSettings | None = None


__all__ = ["ProviderConfig", "ProviderSettings"]
