"""Type definitions for agents."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class AgentConfig:
    """Agent configuration.

    Attributes:
        name: Agent name.
        version: Agent version.
        description: Agent description.
        role: Agent role configuration.
        capabilities: List of required capabilities.
        tools: List of required tools.
        settings: Additional settings.
        metadata: Additional metadata.
    """

    name: str
    version: str
    description: str
    role: dict[str, str]
    capabilities: list[str]
    tools: list[str]
    settings: dict[str, Any]
    metadata: dict[str, Any]


class Capability(Protocol):
    """Capability protocol defining interface for agent capabilities."""

    @property
    def name(self) -> str:
        """Get capability name."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if capability is available."""
        ...

    async def initialize(self) -> None:
        """Initialize capability."""
        ...

    async def cleanup(self) -> None:
        """Cleanup capability resources."""
        ...


class Tool(Protocol):
    """Tool protocol defining interface for agent tools."""

    @property
    def name(self) -> str:
        """Get tool name."""
        ...

    @property
    def description(self) -> str:
        """Get tool description."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if tool is available."""
        ...

    async def execute(self, **kwargs: Any) -> Any:
        """Execute tool with given parameters."""
        ...
