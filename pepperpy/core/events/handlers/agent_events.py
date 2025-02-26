"""Agent event handlers and types.

This module provides event handling for agent-related events:
- Agent creation/deletion
- Agent state changes
- Agent execution events
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import Field

from pepperpy.events.base import Event, EventHandler, EventPriority, EventType
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class AgentEvent(Event):
    """Base class for agent events."""

    agent_id: UUID = Field(..., description="ID of the agent")
    agent_name: str = Field(..., description="Name of the agent")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")

    def __init__(
        self,
        event_type: str,
        priority: EventPriority,
        agent_id: UUID,
        agent_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize agent event."""
        super().__init__(event_type=event_type, priority=priority)
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.metadata = metadata


class AgentCreatedEvent(AgentEvent):
    """Event emitted when a new agent is created."""

    def __init__(
        self,
        agent_id: UUID,
        agent_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize agent created event."""
        super().__init__(
            event_type=str(EventType.AGENT_CREATED),
            priority=EventPriority.NORMAL,
            agent_id=agent_id,
            agent_name=agent_name,
            metadata=metadata,
        )


class AgentRemovedEvent(AgentEvent):
    """Event emitted when an agent is removed."""

    def __init__(
        self,
        agent_id: UUID,
        agent_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize agent removed event."""
        super().__init__(
            event_type=str(EventType.AGENT_REMOVED),
            priority=EventPriority.NORMAL,
            agent_id=agent_id,
            agent_name=agent_name,
            metadata=metadata,
        )


class AgentStateChangedEvent(AgentEvent):
    """Event emitted when an agent's state changes."""

    previous_state: str = Field(..., description="Previous agent state")
    new_state: str = Field(..., description="New agent state")

    def __init__(
        self,
        agent_id: UUID,
        agent_name: str,
        previous_state: str,
        new_state: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize agent state changed event."""
        super().__init__(
            event_type=str(EventType.AGENT_STATE_CHANGED),
            priority=EventPriority.NORMAL,
            agent_id=agent_id,
            agent_name=agent_name,
            metadata=metadata,
        )
        self.previous_state = previous_state
        self.new_state = new_state


class AgentEventHandler(EventHandler):
    """Handler for agent events."""

    @property
    def supported_event_types(self) -> List[str]:
        """Get supported event types.

        Returns:
            List of supported event types
        """
        return [
            str(EventType.AGENT_CREATED),
            str(EventType.AGENT_REMOVED),
            str(EventType.AGENT_STATE_CHANGED),
        ]

    async def handle_event(self, event: Event) -> None:
        """Handle agent events.

        Args:
            event: Agent event to handle
        """
        if not isinstance(event, AgentEvent):
            logger.warning(
                "Invalid event type",
                extra={
                    "expected": "AgentEvent",
                    "received": type(event).__name__,
                },
            )
            return

        # Log event details
        logger.info(
            f"Handling agent event: {event.event_type}",
            extra={
                "agent_id": str(event.agent_id),
                "agent_name": event.agent_name,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # Handle specific event types
        if event.event_type == str(EventType.AGENT_CREATED):
            await self._handle_agent_created(event)  # type: ignore
        elif event.event_type == str(EventType.AGENT_REMOVED):
            await self._handle_agent_removed(event)  # type: ignore
        elif event.event_type == str(EventType.AGENT_STATE_CHANGED):
            await self._handle_agent_state_changed(event)  # type: ignore

    async def _handle_agent_created(self, event: AgentCreatedEvent) -> None:
        """Handle agent created event.

        Args:
            event: Agent created event
        """
        logger.info(
            "Agent created",
            extra={
                "agent_id": str(event.agent_id),
                "agent_name": event.agent_name,
            },
        )

    async def _handle_agent_removed(self, event: AgentRemovedEvent) -> None:
        """Handle agent removed event.

        Args:
            event: Agent removed event
        """
        logger.info(
            "Agent removed",
            extra={
                "agent_id": str(event.agent_id),
                "agent_name": event.agent_name,
            },
        )

    async def _handle_agent_state_changed(
        self, event: AgentStateChangedEvent
    ) -> None:
        """Handle agent state changed event.

        Args:
            event: Agent state changed event
        """
        logger.info(
            "Agent state changed",
            extra={
                "agent_id": str(event.agent_id),
                "agent_name": event.agent_name,
                "previous_state": event.previous_state,
                "new_state": event.new_state,
            },
        )
