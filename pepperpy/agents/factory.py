"""Factory for creating agents in the Pepperpy framework.

This module provides the factory implementation for creating different types
of agents based on configuration.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Type
from uuid import UUID, uuid4

from pepperpy.agents.base import BaseAgent
from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class AgentFactory(BaseComponent):
    """Factory for creating agents.

    This factory is responsible for creating agent instances based on
    configuration and managing their lifecycle.

    Attributes:
        id: Unique identifier for the factory
        metadata: Factory metadata
        _agent_types: Mapping of agent type names to agent classes

    """

    def __init__(
        self,
        id: UUID,
        metadata: Optional[Metadata] = None,
    ) -> None:
        """Initialize the agent factory.

        Args:
            id: Unique identifier for the factory
            metadata: Optional factory metadata

        """
        super().__init__(id, metadata)
        self._agent_types: Dict[str, Type[BaseAgent]] = {}
        self._logger = logger.getChild(self.__class__.__name__)

    def register_agent_type(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type.

        Args:
            name: Name of the agent type
            agent_class: Agent class to register

        Raises:
            ConfigurationError: If agent type is invalid

        """
        if not name:
            raise ConfigurationError("Agent type name is required")
        if not issubclass(agent_class, BaseAgent):
            raise ConfigurationError(f"Invalid agent class: {agent_class.__name__}")

        self._agent_types[name] = agent_class
        self._logger.info("Registered agent type", extra={"type": name})

    async def create_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, str]] = None,
    ) -> BaseAgent:
        """Create an agent instance.

        Args:
            agent_type: Type of agent to create
            config: Optional agent configuration

        Returns:
            Created agent instance

        Raises:
            ConfigurationError: If agent type is not supported

        """
        if not agent_type:
            raise ConfigurationError("Agent type not specified")

        agent_class = self._agent_types.get(agent_type)
        if not agent_class:
            raise ConfigurationError(f"Unsupported agent type: {agent_type}")

        try:
            # Create agent metadata
            now = datetime.utcnow()
            metadata = Metadata(
                created_at=now,
                updated_at=now,
                version="1.0.0",
                tags=[agent_type],
                properties=config or {},
            )

            # Create agent instance
            agent = agent_class(
                id=uuid4(),
                metadata=metadata,
                config=config,
            )

            # Initialize agent
            await agent.initialize()

            self._logger.info(
                "Created agent",
                extra={
                    "type": agent_type,
                    "id": str(agent.id),
                },
            )
            return agent

        except Exception as e:
            self._logger.error(
                "Failed to create agent",
                extra={
                    "type": agent_type,
                    "error": str(e),
                },
            )
            raise ConfigurationError(f"Failed to create agent: {e}") from e

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        self._agent_types.clear()
        self._logger.info("Agent factory cleaned up")

    async def execute(self, **kwargs: Any) -> Any:
        """Execute factory functionality.

        This method implements the BaseComponent interface.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution results

        """
        agent_type = kwargs.get("agent_type")
        config = kwargs.get("config")
        if not agent_type:
            raise ConfigurationError("Agent type is required")
        return await self.create_agent(agent_type, config)

    def validate(self) -> None:
        """Validate factory state.

        Raises:
            ConfigurationError: If factory state is invalid

        """
        super().validate()
        if not isinstance(self._agent_types, dict):
            raise ConfigurationError("Agent types must be a dictionary")
