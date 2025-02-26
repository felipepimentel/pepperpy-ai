"""Workflow event handlers and types.

This module provides event handling for workflow-related events:
- Workflow creation/deletion
- Workflow state changes
- Workflow execution events
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import Field

from pepperpy.events.base import Event, EventHandler, EventPriority, EventType
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class WorkflowEvent(Event):
    """Base class for workflow events."""

    workflow_id: UUID = Field(..., description="ID of the workflow")
    workflow_name: str = Field(..., description="Name of the workflow")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")

    def __init__(
        self,
        event_type: str,
        priority: EventPriority,
        workflow_id: UUID,
        workflow_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize workflow event."""
        super().__init__(event_type=event_type, priority=priority)
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.metadata = metadata


class WorkflowStartedEvent(WorkflowEvent):
    """Event emitted when a workflow starts execution."""

    def __init__(
        self,
        workflow_id: UUID,
        workflow_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize workflow started event."""
        super().__init__(
            event_type=str(EventType.WORKFLOW_STARTED),
            priority=EventPriority.NORMAL,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            metadata=metadata,
        )


class WorkflowCompletedEvent(WorkflowEvent):
    """Event emitted when a workflow completes execution."""

    def __init__(
        self,
        workflow_id: UUID,
        workflow_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize workflow completed event."""
        super().__init__(
            event_type=str(EventType.WORKFLOW_COMPLETED),
            priority=EventPriority.NORMAL,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            metadata=metadata,
        )


class WorkflowFailedEvent(WorkflowEvent):
    """Event emitted when a workflow fails."""

    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")

    def __init__(
        self,
        workflow_id: UUID,
        workflow_name: str,
        error: str,
        error_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize workflow failed event."""
        super().__init__(
            event_type=str(EventType.WORKFLOW_FAILED),
            priority=EventPriority.HIGH,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            metadata=metadata,
        )
        self.error = error
        self.error_type = error_type


class WorkflowEventHandler(EventHandler):
    """Handler for workflow events."""

    @property
    def supported_event_types(self) -> List[str]:
        """Get supported event types.

        Returns:
            List of supported event types
        """
        return [
            str(EventType.WORKFLOW_STARTED),
            str(EventType.WORKFLOW_COMPLETED),
            str(EventType.WORKFLOW_FAILED),
        ]

    async def handle_event(self, event: Event) -> None:
        """Handle workflow events.

        Args:
            event: Workflow event to handle
        """
        if not isinstance(event, WorkflowEvent):
            logger.warning(
                "Invalid event type",
                extra={
                    "expected": "WorkflowEvent",
                    "received": type(event).__name__,
                },
            )
            return

        # Log event details
        logger.info(
            f"Handling workflow event: {event.event_type}",
            extra={
                "workflow_id": str(event.workflow_id),
                "workflow_name": event.workflow_name,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # Handle specific event types
        if event.event_type == str(EventType.WORKFLOW_STARTED):
            await self._handle_workflow_started(event)  # type: ignore
        elif event.event_type == str(EventType.WORKFLOW_COMPLETED):
            await self._handle_workflow_completed(event)  # type: ignore
        elif event.event_type == str(EventType.WORKFLOW_FAILED):
            await self._handle_workflow_failed(event)  # type: ignore

    async def _handle_workflow_started(self, event: WorkflowStartedEvent) -> None:
        """Handle workflow started event.

        Args:
            event: Workflow started event
        """
        logger.info(
            "Workflow started",
            extra={
                "workflow_id": str(event.workflow_id),
                "workflow_name": event.workflow_name,
            },
        )

    async def _handle_workflow_completed(self, event: WorkflowCompletedEvent) -> None:
        """Handle workflow completed event.

        Args:
            event: Workflow completed event
        """
        logger.info(
            "Workflow completed",
            extra={
                "workflow_id": str(event.workflow_id),
                "workflow_name": event.workflow_name,
            },
        )

    async def _handle_workflow_failed(self, event: WorkflowFailedEvent) -> None:
        """Handle workflow failed event.

        Args:
            event: Workflow failed event
        """
        logger.error(
            "Workflow failed",
            extra={
                "workflow_id": str(event.workflow_id),
                "workflow_name": event.workflow_name,
                "error": event.error,
                "error_type": event.error_type,
            },
        )
