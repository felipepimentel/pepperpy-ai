"""Provider configuration module."""

from dataclasses import dataclass
from typing import Any

from pepperpy_core.types import BaseConfig


@dataclass
class ProviderConfig(BaseConfig):
    """Base provider configuration."""

    name: str
    version: str
    model: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    metadata: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
