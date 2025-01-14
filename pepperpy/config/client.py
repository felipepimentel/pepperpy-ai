"""Client configuration module."""

from dataclasses import dataclass, field
from typing import Any

from pepperpy_core.types import BaseConfig


@dataclass
class ClientConfig(BaseConfig):
    """Client configuration."""

    name: str
    version: str
    provider: str
    model: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
