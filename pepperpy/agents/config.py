"""Agent configuration module."""

from dataclasses import dataclass, field
from typing import Any

from pepperpy.types import BaseConfig


@dataclass
class BaseAgentConfig:
    """Base agent configuration.

    Attributes:
        name: Agent name.
        version: Agent version.
        provider: Agent provider type.
    """

    name: str
    version: str
    provider: str


@dataclass
class AgentConfig(BaseConfig, BaseAgentConfig):
    """Agent configuration.

    Attributes:
        description: Optional agent description.
        settings: Optional agent-specific settings.
        metadata: Optional metadata about the agent.
    """

    description: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
