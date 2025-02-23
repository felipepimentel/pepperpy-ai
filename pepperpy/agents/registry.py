"""Agent registry module for the Pepperpy framework.

This module provides the agent registry functionality for managing different agent types.
It defines the registry class, agent type registration, and agent creation.
"""

from typing import Any, Dict, Optional, Type

from pepperpy.agents.autonomous import AutonomousAgent, AutonomousAgentConfig
from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.agents.interactive import InteractiveAgent, InteractiveAgentConfig
from pepperpy.agents.workflow import WorkflowAgent, WorkflowAgentConfig
from pepperpy.core.errors import AgentError
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class AgentRegistry:
    """Registry for managing agent types.

    This class provides functionality for registering agent types,
    creating agent instances, and managing agent configurations.
    """

    def __init__(self) -> None:
        """Initialize agent registry."""
        self._agent_types: Dict[str, Type[BaseAgent]] = {}
        self._config_types: Dict[str, Type[AgentConfig]] = {}

        # Register built-in agent types
        self.register_agent_type(
            "autonomous",
            AutonomousAgent,
            AutonomousAgentConfig,
        )
        self.register_agent_type(
            "interactive",
            InteractiveAgent,
            InteractiveAgentConfig,
        )
        self.register_agent_type(
            "workflow",
            WorkflowAgent,
            WorkflowAgentConfig,
        )

    def register_agent_type(
        self,
        agent_type: str,
        agent_class: Type[BaseAgent],
        config_class: Type[AgentConfig],
    ) -> None:
        """Register a new agent type.

        Args:
            agent_type: Type identifier
            agent_class: Agent implementation class
            config_class: Agent configuration class

        Raises:
            AgentError: If agent type is already registered
        """
        if agent_type in self._agent_types:
            raise AgentError(f"Agent type already registered: {agent_type}")

        self._agent_types[agent_type] = agent_class
        self._config_types[agent_type] = config_class

    def create_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseAgent:
        """Create an agent instance.

        Args:
            agent_type: Type of agent to create
            config: Optional agent configuration

        Returns:
            Agent instance

        Raises:
            AgentError: If agent type is not registered
        """
        agent_class = self._agent_types.get(agent_type)
        if not agent_class:
            raise AgentError(f"Agent type not registered: {agent_type}")

        config_class = self._config_types[agent_type]
        agent_config = None

        if config:
            # Create configuration instance
            try:
                agent_config = config_class(**config)
            except Exception as e:
                raise AgentError(f"Invalid configuration for {agent_type}: {e}") from e

        # Create agent instance
        try:
            return agent_class(config=agent_config)
        except Exception as e:
            raise AgentError(f"Failed to create {agent_type} agent: {e}") from e

    def get_agent_types(self) -> Dict[str, Type[BaseAgent]]:
        """Get registered agent types.

        Returns:
            Dictionary of agent types
        """
        return self._agent_types.copy()

    def get_config_types(self) -> Dict[str, Type[AgentConfig]]:
        """Get registered configuration types.

        Returns:
            Dictionary of configuration types
        """
        return self._config_types.copy()


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance.

    Returns:
        Agent registry instance
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
