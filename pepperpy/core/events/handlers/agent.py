"""Agent event handler.

This module provides an event handler for agent-related events.
"""

from typing import Any

from pepperpy.events.base import Event, EventHandler
from pepperpy.monitoring import logger


class AgentEventHandler(EventHandler):
    """Agent event handler."""

    def __init__(self, name: str) -> None:
        """Initialize agent event handler.

        Args:
            name: Handler name
        """
        super().__init__(name)
        self._agents: dict[str, dict[str, Any]] = {}

    async def _handle_event(self, event: Event) -> None:
        """Handle agent event.

        Args:
            event: Agent event to handle
        """
        try:
            if event.type == "agent.created":
                await self._handle_agent_created(event)
            elif event.type == "agent.removed":
                await self._handle_agent_removed(event)
            elif event.type == "agent.state.changed":
                await self._handle_agent_state_changed(event)
            else:
                logger.warning(f"Unknown agent event type: {event.type}")

        except Exception as e:
            logger.error(f"Failed to handle agent event: {e}")
            raise

    async def _handle_agent_created(self, event: Event) -> None:
        """Handle agent created event.

        Args:
            event: Agent created event
        """
        agent_id = event.data.get("agent_id")
        if not agent_id:
            logger.error("Missing agent ID in agent created event")
            return

        self._agents[agent_id] = {
            "state": "created",
            "metadata": event.metadata,
            **event.data,
        }

        logger.info(f"Agent created: {agent_id}")

    async def _handle_agent_removed(self, event: Event) -> None:
        """Handle agent removed event.

        Args:
            event: Agent removed event
        """
        agent_id = event.data.get("agent_id")
        if not agent_id:
            logger.error("Missing agent ID in agent removed event")
            return

        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Agent removed: {agent_id}")
        else:
            logger.warning(f"Agent not found: {agent_id}")

    async def _handle_agent_state_changed(self, event: Event) -> None:
        """Handle agent state changed event.

        Args:
            event: Agent state changed event
        """
        agent_id = event.data.get("agent_id")
        new_state = event.data.get("state")

        if not agent_id or not new_state:
            logger.error("Missing agent ID or state in agent state changed event")
            return

        if agent_id in self._agents:
            self._agents[agent_id]["state"] = new_state
            logger.info(f"Agent {agent_id} state changed to: {new_state}")
        else:
            logger.warning(f"Agent not found: {agent_id}")


# Export public API
__all__ = ["AgentEventHandler"]
