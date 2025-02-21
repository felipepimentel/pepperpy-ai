"""Agent registry module.

This module provides the registry for managing agents in the system.
It handles agent registration, retrieval, and lifecycle management.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pepperpy.agents.base import BaseAgent
from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class AgentRegistry:
    """Registry for managing agents."""

    def __init__(self):
        """Initialize agent registry."""
        self._agents: Dict[str, BaseAgent] = {}

    async def register(self, agent: BaseAgent) -> str:
        """Register an agent.

        Args:
            agent: Agent to register

        Returns:
            str: Agent ID

        Raises:
            PepperpyError: If registration fails
        """
        try:
            # Generate agent ID
            agent_id = f"{agent.name}-{datetime.utcnow().isoformat()}"

            # Store agent
            self._agents[agent_id] = agent

            logger.info(
                "Registered agent",
                extra={
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.type,
                },
            )

            return agent_id

        except Exception as e:
            raise PepperpyError(
                message=f"Failed to register agent: {e}",
                details={
                    "agent_name": agent.name,
                    "agent_type": agent.type,
                },
                recovery_hint="Check agent configuration and try again",
            )

    async def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Optional[BaseAgent]: Agent if found, None otherwise

        Raises:
            PepperpyError: If retrieval fails
        """
        try:
            return self._agents.get(agent_id)

        except Exception as e:
            raise PepperpyError(
                message=f"Failed to get agent: {e}",
                details={"agent_id": agent_id},
                recovery_hint="Check agent ID and try again",
            )

    async def list(
        self,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[BaseAgent]:
        """List registered agents.

        Args:
            filters: Optional filters to apply

        Returns:
            List[BaseAgent]: List of matching agents

        Raises:
            PepperpyError: If listing fails
        """
        try:
            result = []
            for agent in self._agents.values():
                if filters:
                    matches = True
                    for key, value in filters.items():
                        if getattr(agent, key, None) != value:
                            matches = False
                            break
                    if not matches:
                        continue
                result.append(agent)

            return result

        except Exception as e:
            raise PepperpyError(
                message=f"Failed to list agents: {e}",
                details={"filters": filters},
                recovery_hint="Check filter criteria and try again",
            )

    async def update(self, agent_id: str, agent: BaseAgent) -> None:
        """Update an agent.

        Args:
            agent_id: Agent ID
            agent: Updated agent

        Raises:
            PepperpyError: If update fails
        """
        try:
            if agent_id not in self._agents:
                raise PepperpyError(
                    message=f"Agent not found: {agent_id}",
                    details={"agent_id": agent_id},
                    recovery_hint="Check agent ID and try again",
                )

            self._agents[agent_id] = agent

            logger.info(
                "Updated agent",
                extra={
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.type,
                },
            )

        except PepperpyError:
            raise
        except Exception as e:
            raise PepperpyError(
                message=f"Failed to update agent: {e}",
                details={
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.type,
                },
                recovery_hint="Check agent configuration and try again",
            )

    async def delete(self, agent_id: str) -> None:
        """Delete an agent.

        Args:
            agent_id: Agent ID

        Raises:
            PepperpyError: If deletion fails
        """
        try:
            if agent_id not in self._agents:
                raise PepperpyError(
                    message=f"Agent not found: {agent_id}",
                    details={"agent_id": agent_id},
                    recovery_hint="Check agent ID and try again",
                )

            agent = self._agents.pop(agent_id)

            logger.info(
                "Deleted agent",
                extra={
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "agent_type": agent.type,
                },
            )

        except PepperpyError:
            raise
        except Exception as e:
            raise PepperpyError(
                message=f"Failed to delete agent: {e}",
                details={"agent_id": agent_id},
                recovery_hint="Check agent ID and try again",
            )
