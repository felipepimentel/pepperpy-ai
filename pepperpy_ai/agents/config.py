"""Agent configuration module."""

from dataclasses import dataclass, field
from typing import Any

from pepperpy_core.types import BaseConfig


@dataclass
class AgentConfig(BaseConfig):
    """Agent configuration."""

    name: str
    version: str
    provider: str
    model: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
