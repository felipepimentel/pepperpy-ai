"""Base classes for AI agents.

This module provides the base classes and utilities for creating AI agents.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pepperpy.providers.base import Provider


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""

    provider: Optional[Provider] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values for parameters."""
        if self.parameters is None:
            self.parameters = {}


class Agent:
    """Base class for AI agents."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent.

        Args:
        ----
            config: Configuration for the agent.

        """
        self.config = config
        self.name = "Base Agent"
        self.description = "Base class for AI agents"

    async def execute(self, prompt: str) -> str:
        """Execute the agent with a given prompt.

        Args:
        ----
            prompt: The prompt to execute.

        Returns:
        -------
            The agent's response.

        """
        if not self.config.provider:
            raise ValueError("No provider configured for agent")
        return await self.config.provider.generate(prompt, self.config.parameters)


class AgentRegistry:
    """Registry for managing and loading agents."""

    _agents: Dict[str, Agent] = {}

    @classmethod
    def register(cls, name: str, agent: Agent) -> None:
        """Register an agent.

        Args:
        ----
            name: Name to register the agent under.
            agent: The agent instance to register.

        """
        cls._agents[name] = agent

    @classmethod
    def get(cls, name: str) -> Agent:
        """Get a registered agent by name.

        Args:
        ----
            name: Name of the agent to get.

        Returns:
        -------
            The registered agent.

        Raises:
        ------
            KeyError: If no agent is registered with the given name.

        """
        if name not in cls._agents:
            raise KeyError(f"No agent registered with name: {name}")
        return cls._agents[name]

    @classmethod
    def list(cls) -> Dict[str, Agent]:
        """List all registered agents.

        Returns
        -------
            Dictionary of registered agents.

        """
        return cls._agents.copy()
