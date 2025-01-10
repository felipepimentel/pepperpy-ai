"""Provider configuration."""

from dataclasses import dataclass, field
from typing import Any

from ..config.base import BaseConfigData


@dataclass
class ProviderConfig(BaseConfigData):
    """Provider configuration."""

    name: str
    provider: str
    model: str
    api_key: str
    api_base: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    metadata: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
