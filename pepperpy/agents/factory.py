"""Factory for creating agents in the Pepperpy framework.

This module provides the factory implementation for creating different types
of agents based on configuration.
"""

from typing import TYPE_CHECKING, Dict, Type, cast

from pepperpy.core.base import AgentConfig, BaseAgent
from pepperpy.core.errors import ConfigurationError
from pepperpy.core.factory import Factory
from pepperpy.core.types import PepperpyClientProtocol
from pepperpy.monitoring import logger as log

if TYPE_CHECKING:
    pass

# Type variables for agent creation
T_Agent = Type[BaseAgent]


class AgentFactory(Factory[BaseAgent]):
    """Factory for creating agents.

    This factory is responsible for creating agent instances based on
    configuration and managing their lifecycle.

    Attributes
    ----------
        client: The Pepperpy client instance
        _agent_types: Mapping of agent type names to agent classes

    """

    def __init__(self, client: PepperpyClientProtocol) -> None:
        """Initialize the agent factory.

        Args:
        ----
            client: The Pepperpy client instance

        """
        super().__init__()
        self.client = client
        self._agent_types: Dict[str, T_Agent] = {}

    def register_agent_type(self, name: str, agent_class: T_Agent) -> None:
        """Register an agent type.

        Args:
        ----
            name: Name of the agent type
            agent_class: Agent class to register

        """
        self._agent_types[name] = agent_class
        log.info(f"Registered agent type: {name}")

    async def create(self, agent_type: str) -> BaseAgent:
        """Create an agent instance.

        Args:
        ----
            agent_type: Type of agent to create

        Returns:
        -------
            Created agent instance

        Raises:
        ------
            ConfigurationError: If agent type is not supported

        """
        if not agent_type:
            raise ConfigurationError("Agent type not specified")

        agent_class = self._agent_types.get(agent_type)
        if not agent_class:
            raise ConfigurationError(f"Unsupported agent type: {agent_type}")

        try:
            # Create agent configuration
            config = AgentConfig(
                type=agent_type,
                name=agent_type,
                description="",
                version="0.1.0",
                settings={},
                metadata={},
            )

            agent = agent_class(
                client=cast(PepperpyClientProtocol, self.client), config=config
            )
            log.info(f"Created agent of type: {agent_type}")
            return agent
        except Exception as e:
            log.error(
                "Failed to create agent",
                error=str(e),
                agent_type=agent_type,
            )
            raise ConfigurationError(f"Failed to create agent: {e}") from e

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        self._agent_types.clear()
        log.info("Agent factory cleaned up")
