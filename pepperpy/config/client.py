"""Client configuration module."""

from dataclasses import dataclass, field
from typing import Any

from pepperpy.types import BaseConfig


@dataclass
class BaseClientConfig:
    """Base client configuration.

    Attributes:
        name: Client name.
        version: Client version.
        provider: Client provider type.
    """

    name: str
    version: str
    provider: str


@dataclass
class ClientConfig(BaseConfig, BaseClientConfig):
    """Client configuration.

    Attributes:
        description: Optional client description.
        settings: Optional client-specific settings.
        metadata: Optional metadata about the client.
    """

    description: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
