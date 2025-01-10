"""Agent configuration."""

from dataclasses import dataclass, field

from ..agents.types import AgentRole
from .base import BaseConfigData, JsonDict


@dataclass
class AgentConfig(BaseConfigData):
    """Agent configuration."""

    # Required fields first (no defaults)
    name: str
    role: AgentRole

    # Optional fields (with defaults)
    description: str | None = None
    capabilities: dict[str, str] = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
