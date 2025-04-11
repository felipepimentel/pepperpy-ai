"""Agent registry for managing agent instances.

This module provides a registry for managing agent instances.
"""

import inspect
import logging
from typing import Any

from .base import AgentCapability, AgentContext, BaseAgent
from .specialized import (
    AssistantAgent,
    Orchestrator,
    PlanningAgent,
    RAGAgent,
    ToolAgent,
)

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for managing agent instances."""

    def __init__(self):
        """Initialize the agent registry."""
        self.agents: dict[str, BaseAgent] = {}
        self.agent_types: dict[str, type[BaseAgent]] = {
            "assistant": AssistantAgent,
            "rag": RAGAgent,
            "tool": ToolAgent,
            "planning": PlanningAgent,
            "orchestrator": Orchestrator,
        }
        self.context = AgentContext(session_id="agent_registry")
        self.is_initialized = False

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the agent registry with configuration.

        Args:
            config: Registry configuration
        """
        if self.is_initialized:
            return

        # Set up context
        context_config = config.get("context", {})
        for key, value in context_config.items():
            # Use _data directly since context.set is async
            self.context._data[key] = value

        # Create agents
        agents_config = config.get("agents", [])
        for agent_config in agents_config:
            agent_type = agent_config.get("type")
            if not agent_type or agent_type not in self.agent_types:
                logger.warning(f"Unknown agent type: {agent_type}")
                continue

            agent_id = agent_config.get("id")
            if not agent_id:
                logger.warning("Agent config missing 'id'")
                continue

            try:
                await self.create_agent(agent_id, agent_type, agent_config)
            except Exception as e:
                logger.exception(f"Error creating agent {agent_id}: {e!s}")

        self.is_initialized = True
        logger.info(f"Initialized agent registry with {len(self.agents)} agents")

    async def create_agent(
        self, agent_id: str, agent_type: str, config: dict[str, Any]
    ) -> BaseAgent | None:
        """Create a new agent.

        Args:
            agent_id: Agent ID
            agent_type: Agent type
            config: Agent configuration

        Returns:
            Created agent or None if creation failed
        """
        if agent_id in self.agents:
            logger.warning(f"Agent with ID {agent_id} already exists")
            return None

        if agent_type not in self.agent_types:
            logger.warning(f"Unknown agent type: {agent_type}")
            return None

        # Create agent
        agent_class = self.agent_types[agent_type]
        agent_kwargs = {k: v for k, v in config.items() if k not in ["type"]}

        # Check if the agent class constructor expects 'id' or 'agent_id'
        sig = inspect.signature(agent_class.__init__)
        param_names = [param for param in sig.parameters]

        # Determine if we should use 'id' or 'agent_id'
        if "id" in param_names and "agent_id" not in param_names:
            agent_kwargs["id"] = agent_id
        else:
            agent_kwargs["agent_id"] = agent_id

        # Only add name if not already in kwargs
        if "name" not in agent_kwargs:
            agent_kwargs["name"] = agent_id

        # Create agent with the appropriate parameters
        try:
            agent = agent_class(**agent_kwargs)
        except TypeError as e:
            logger.exception(f"Error creating agent {agent_id}: {e}")
            return None

        # Initialize agent
        try:
            await agent.initialize(self.context)
            self.agents[agent_id] = agent
            logger.info(f"Created agent {agent_id} of type {agent_type}")
            return agent
        except Exception as e:
            logger.exception(f"Error initializing agent {agent_id}: {e!s}")
            return None

    async def get_agent(self, agent_id: str) -> BaseAgent | None:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_id)

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if the agent was deleted, False otherwise
        """
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        try:
            await agent.shutdown()
        except Exception as e:
            logger.exception(f"Error shutting down agent {agent_id}: {e!s}")

        del self.agents[agent_id]
        logger.info(f"Deleted agent {agent_id}")
        return True

    async def get_agents_by_capability(
        self, capability: AgentCapability
    ) -> list[BaseAgent]:
        """Get agents with a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            List of agents with the specified capability
        """
        return [
            agent for agent in self.agents.values() if capability in agent.capabilities
        ]

    async def get_agent_ids(self) -> list[str]:
        """Get all agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self.agents.keys())

    async def get_agent_types(self) -> list[str]:
        """Get all available agent types.

        Returns:
            List of agent types
        """
        return list(self.agent_types.keys())

    async def register_agent_type(
        self, type_name: str, agent_class: type[BaseAgent]
    ) -> None:
        """Register a new agent type.

        Args:
            type_name: Type name
            agent_class: Agent class
        """
        if type_name in self.agent_types:
            logger.warning(f"Agent type {type_name} already registered")
            return

        self.agent_types[type_name] = agent_class
        logger.info(f"Registered agent type {type_name}")

    async def shutdown(self) -> None:
        """Shut down all agents and clean up resources."""
        for agent_id, agent in list(self.agents.items()):
            try:
                await agent.shutdown()
            except Exception as e:
                logger.exception(f"Error shutting down agent {agent_id}: {e!s}")

        self.agents.clear()
        # Use _data directly since context.clear is async
        self.context._data.clear()
        self.context._shared_memory.clear()
        self.context._history.clear()
        self.context._tools.clear()
        self.is_initialized = False
        logger.info("Agent registry shut down")
