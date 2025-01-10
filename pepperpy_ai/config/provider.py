"""Provider configuration."""

from dataclasses import dataclass, field

from .base import BaseConfigData, JsonDict


@dataclass
class ProviderConfig(BaseConfigData):
    """Provider configuration."""

    # Required fields first (no defaults)
    name: str
    provider: str
    model: str
    api_key: str

    # Optional fields (with defaults)
    api_base: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
