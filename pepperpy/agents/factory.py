"""Agent factory implementation."""

from pathlib import Path
from typing import Any, TypeVar

from .base import BaseAgent
from .loader import AgentLoader
from .types import AgentConfig

T = TypeVar("T", bound=BaseAgent)


class AgentFactory:
    """Factory for creating agent instances."""

    def __init__(self, base_path: str | Path | None = None) -> None:
        """Initialize agent factory.

        Args:
            base_path: Base path for agent definitions.
        """
        self._loader = AgentLoader(base_path)
        self._agent_types: dict[str, type[BaseAgent]] = {}

    def register(self, name: str, agent_cls: type[T]) -> None:
        """Register agent type.

        Args:
            name: Agent type name.
            agent_cls: Agent class.
        """
        self._agent_types[name] = agent_cls

    def create(self, name: str, **kwargs: Any) -> BaseAgent:
        """Create agent instance by name.

        Args:
            name: Agent type name.
            **kwargs: Additional configuration.

        Returns:
            Agent instance.

        Raises:
            ValueError: If agent type is not registered.
        """
        if name not in self._agent_types:
            raise ValueError(f"Unknown agent type: {name}")

        agent_cls = self._agent_types[name]
        config = AgentConfig(
            name=name,
            version=str(kwargs.get("version", "1.0.0")),
            description=str(kwargs.get("description", "")),
            role=dict(kwargs.get("role", {})),
            capabilities=list(map(str, kwargs.get("capabilities", []))),
            tools=list(map(str, kwargs.get("tools", []))),
            settings=dict(kwargs.get("settings", {})),
            metadata=dict(kwargs.get("metadata", {})),
        )
        return agent_cls(config)

    def from_yaml(self, path: str) -> BaseAgent:
        """Create agent from YAML definition.

        Args:
            path: Path to agent YAML file.

        Returns:
            Agent instance.

        Raises:
            FileNotFoundError: If agent file doesn't exist.
            ValueError: If agent type is not registered.
        """
        config = self._loader.load(path)
        return self.create(
            config.name,
            version=config.version,
            description=config.description,
            role=config.role,
            capabilities=config.capabilities,
            tools=config.tools,
            settings=config.settings,
            metadata=config.metadata,
        )

    def discover(self, pattern: str | None = None) -> list[str]:
        """Discover available agent definitions.

        Args:
            pattern: Optional glob pattern to filter agents.

        Returns:
            List of available agent paths.
        """
        return self._loader.discover(pattern)
