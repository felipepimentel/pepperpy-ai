"""Agent factory module for the Pepperpy framework.

This module provides the agent factory functionality for creating agent instances.
It defines the factory class, agent creation, and configuration validation.
"""

from typing import Any, Dict, Optional

from pepperpy.agents.base import BaseAgent
from pepperpy.agents.registry import get_agent_registry
from pepperpy.core.errors import AgentError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """Factory for creating agent instances.

    This class provides functionality for creating and configuring
    different types of agents using the agent registry.
    """

    def __init__(self) -> None:
        """Initialize agent factory."""
        self._registry = get_agent_registry()

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
            AgentError: If agent creation fails
        """
        try:
            # Create agent using registry
            agent = self._registry.create_agent(agent_type, config)

            logger.info(
                "Created agent",
                extra={
                    "agent_type": agent_type,
                    "agent_name": agent.config.name,
                },
            )

            return agent

        except Exception as e:
            raise AgentError(
                f"Failed to create agent: {e}",
                details={
                    "agent_type": agent_type,
                    "config": config,
                },
            )

    def create_autonomous_agent(
        self,
        name: str,
        task_types: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> BaseAgent:
        """Create an autonomous agent.

        Args:
            name: Agent name
            task_types: List of supported task types
            **kwargs: Additional configuration options

        Returns:
            Autonomous agent instance
        """
        config = {
            "name": name,
            "task_types": task_types or [],
            **kwargs,
        }
        return self.create_agent("autonomous", config)

    def create_interactive_agent(
        self,
        name: str,
        conversation_types: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> BaseAgent:
        """Create an interactive agent.

        Args:
            name: Agent name
            conversation_types: List of supported conversation types
            **kwargs: Additional configuration options

        Returns:
            Interactive agent instance
        """
        config = {
            "name": name,
            "conversation_types": conversation_types or [],
            **kwargs,
        }
        return self.create_agent("interactive", config)

    def create_workflow_agent(
        self,
        name: str,
        step_types: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> BaseAgent:
        """Create a workflow agent.

        Args:
            name: Agent name
            step_types: List of supported step types
            **kwargs: Additional configuration options

        Returns:
            Workflow agent instance
        """
        config = {
            "name": name,
            "step_types": step_types or [],
            **kwargs,
        }
        return self.create_agent("workflow", config)


# Global factory instance
_factory: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """Get the global agent factory instance.

    Returns:
        Agent factory instance
    """
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory
