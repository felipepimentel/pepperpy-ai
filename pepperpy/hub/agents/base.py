"""Base classes for AI agents.

This module provides the base classes and utilities for creating AI agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pepperpy.monitoring import logger
from pepperpy.providers.base import Provider

T = TypeVar("T")


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""

    provider: Optional[Provider] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    name: str = "Unnamed Agent"
    description: str = "No description provided"
    version: str = "0.1.0"
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values for parameters."""
        if not isinstance(self.parameters, dict):
            self.parameters = {}
        if not isinstance(self.capabilities, list):
            self.capabilities = []


def require_provider(f):
    """Decorator to ensure provider is configured before executing method."""

    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        if not self.config.provider:
            raise ValueError(f"No provider configured for agent {self.config.name}")
        return await f(self, *args, **kwargs)

    return wrapper


class Agent(ABC, Generic[T]):
    """Base class for AI agents with enhanced functionality."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent.

        Args:
        ----
            config: Configuration for the agent.

        """
        self.config = config
        self.log = logger.bind(agent=config.name)

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name

    @property
    def description(self) -> str:
        """Get agent description."""
        return self.config.description

    @property
    def version(self) -> str:
        """Get agent version."""
        return self.config.version

    @property
    def capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.config.capabilities

    @require_provider
    async def execute(self, prompt: str, **kwargs) -> str:
        """Execute the agent with a given prompt.

        Args:
        ----
            prompt: The prompt to execute.
            **kwargs: Additional parameters to pass to the provider.

        Returns:
        -------
            The agent's response.

        """
        self.log.debug("Executing prompt", prompt=prompt[:100] + "...")
        params = {**self.config.parameters, **kwargs}
        assert self.config.provider is not None  # for type checker
        return await self.config.provider.generate(prompt, params)

    @abstractmethod
    async def run(self, input_data: T) -> Any:
        """Run the agent's main functionality.

        This method should be implemented by each agent to provide
        a high-level interface to its capabilities.

        Args:
        ----
            input_data: Input data for the agent.

        Returns:
        -------
            The agent's output.

        """
        raise NotImplementedError

    async def run_sync(self, input_data: T) -> Any:
        """Synchronous version of run method.

        This is a convenience method for users who don't want to deal
        with async/await syntax.

        Args:
        ----
            input_data: Input data for the agent.

        Returns:
        -------
            The agent's output.

        """
        import asyncio

        return asyncio.run(self.run(input_data))

    def validate_capabilities(self, required: List[str]) -> None:
        """Validate that the agent has the required capabilities.

        Args:
        ----
            required: List of required capability names.

        Raises:
        ------
            ValueError: If any required capability is missing.

        """
        missing = [cap for cap in required if cap not in self.capabilities]
        if missing:
            raise ValueError(
                f"Agent {self.name} missing required capabilities: {missing}"
            )

    def __str__(self) -> str:
        """Get string representation of the agent."""
        return f"{self.name} (v{self.version})"

    def __repr__(self) -> str:
        """Get detailed string representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"version='{self.version}', "
            f"capabilities={self.capabilities}"
            f")"
        )


class AgentRegistry:
    """Registry for managing and loading agents."""

    _agents: Dict[str, Dict[str, Agent]] = {}

    @classmethod
    def register(cls, name: str, agent: Agent, version: Optional[str] = None) -> None:
        """Register an agent.

        Args:
        ----
            name: Name to register the agent under.
            agent: The agent instance to register.
            version: Optional version string.

        """
        if name not in cls._agents:
            cls._agents[name] = {}

        version = version or agent.version
        cls._agents[name][version] = agent

    @classmethod
    def get(cls, name: str, version: Optional[str] = None) -> Agent:
        """Get a registered agent by name and version.

        Args:
        ----
            name: Name of the agent to get.
            version: Optional version string.

        Returns:
        -------
            The registered agent.

        Raises:
        ------
            KeyError: If no agent is registered with the given name/version.

        """
        if name not in cls._agents:
            raise KeyError(f"No agent registered with name: {name}")

        agents = cls._agents[name]
        if not version:
            # Get latest version
            version = max(agents.keys())

        if version not in agents:
            raise KeyError(
                f"No agent version {version} found for {name}. "
                f"Available versions: {list(agents.keys())}"
            )

        return agents[version]

    @classmethod
    def list(cls) -> Dict[str, Dict[str, Agent]]:
        """List all registered agents.

        Returns
        -------
            Dictionary of registered agents by name and version.

        """
        return cls._agents.copy()
