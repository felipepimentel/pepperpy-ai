"""Hub event types and handlers.

This module provides event types and handlers for Hub operations.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.types import ComponentState
from pepperpy.events.base import Event, EventHandler, EventType
from pepperpy.events.hooks import hook_manager
from pepperpy.hub.base import HubConfig
from pepperpy.hub.errors import HubError
from pepperpy.monitoring import logger, metrics

# Configure logging
logger = logger.getChild(__name__)


class HubEventMetadata(BaseModel):
    """Metadata for Hub events."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "hub"
    operation: str
    details: Dict[str, Any] = Field(default_factory=dict)


class HubEvent(Event):
    """Base class for Hub events."""

    def __init__(
        self,
        event_type: EventType,
        hub_name: str,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a hub event.

        Args:
            event_type: Type of event
            hub_name: Name of the hub
            operation: Operation being performed
            metadata: Optional additional metadata
        """
        event_metadata = HubEventMetadata(
            operation=operation,
            details=metadata or {},
        )
        super().__init__(
            event_type=str(event_type),
            metadata=event_metadata.dict(),
        )
        self.hub_name = hub_name
        self.operation = operation

    @property
    def event_metadata(self) -> HubEventMetadata:
        """Get event metadata.

        Returns:
            Event metadata
        """
        return HubEventMetadata(**self.metadata)


class HubLifecycleEvent(HubEvent):
    """Event for Hub lifecycle changes."""

    def __init__(
        self,
        hub_name: str,
        operation: str,
        config: HubConfig,
        state: ComponentState,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a lifecycle event.

        Args:
            hub_name: Name of the hub
            operation: Operation being performed
            config: Hub configuration
            state: New component state
            metadata: Optional additional metadata
        """
        super().__init__(
            event_type=EventType.COMPONENT_CREATED,
            hub_name=hub_name,
            operation=operation,
            metadata=metadata,
        )
        self.config = config
        self.state = state


class HubArtifactEvent(HubEvent):
    """Event for Hub artifact operations."""

    def __init__(
        self,
        hub_name: str,
        operation: str,
        artifact_id: UUID,
        artifact_type: str,
        version: str,
        visibility: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize an artifact event.

        Args:
            hub_name: Name of the hub
            operation: Operation being performed
            artifact_id: ID of the artifact
            artifact_type: Type of artifact
            version: Artifact version
            visibility: Artifact visibility
            metadata: Optional additional metadata
        """
        super().__init__(
            event_type=EventType.COMPONENT_CREATED,
            hub_name=hub_name,
            operation=operation,
            metadata=metadata,
        )
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.version = version
        self.visibility = visibility


class HubEventHandler(EventHandler):
    """Handler for Hub events."""

    def __init__(self) -> None:
        """Initialize the event handler."""
        super().__init__()
        self._events_counter = None
        self._errors_counter = None
        self._lifecycle_counter = None
        self._artifact_counter = None
        self._hook_manager = hook_manager

    async def initialize(self) -> None:
        """Initialize metrics and hooks."""
        metrics_manager = metrics.MetricsManager.get_instance()

        # Initialize metrics
        self._events_counter = await metrics_manager.create_counter(
            "hub_events_total",
            "Total number of Hub events processed",
            labels={"type": "hub"},
        )
        self._errors_counter = await metrics_manager.create_counter(
            "hub_errors_total",
            "Total number of Hub event errors",
            labels={"type": "hub"},
        )
        self._lifecycle_counter = await metrics_manager.create_counter(
            "hub_lifecycle_events_total",
            "Total number of Hub lifecycle events",
            labels={"type": "hub"},
        )
        self._artifact_counter = await metrics_manager.create_counter(
            "hub_artifact_events_total",
            "Total number of Hub artifact events",
            labels={"type": "hub"},
        )

    async def handle_event(self, event: Event) -> None:
        """Route events to specific handlers.

        Args:
            event: Event to handle

        Raises:
            ValueError: If event is not a Hub event
            HubError: If there is an error handling the event
        """
        if not isinstance(event, HubEvent):
            if self._errors_counter is not None:
                self._errors_counter.record(1)
            raise ValueError(f"Expected HubEvent, got {type(event)}")

        try:
            # Trigger pre-event hooks
            self._hook_manager.trigger(
                f"hub.pre_event.{event.event_type}", {"event": event}
            )

            if isinstance(event, HubLifecycleEvent):
                await self._handle_lifecycle_event(event)
            elif isinstance(event, HubArtifactEvent):
                await self._handle_artifact_event(event)
            else:
                logger.warning(
                    "Unhandled Hub event type",
                    extra={
                        "event_type": event.event_type,
                        "hub_name": event.hub_name,
                        "operation": event.operation,
                        "event_class": type(event).__name__,
                    },
                )

            if self._events_counter is not None:
                self._events_counter.record(1)

            # Trigger post-event hooks
            self._hook_manager.trigger(
                f"hub.post_event.{event.event_type}",
                {"event": event, "status": "success"},
            )

        except Exception as e:
            if self._errors_counter is not None:
                self._errors_counter.record(1)

            # Log error details
            logger.error(
                "Error handling Hub event",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "hub_name": event.hub_name,
                    "operation": event.operation,
                },
                exc_info=True,
            )

            # Trigger error hooks
            self._hook_manager.trigger(
                f"hub.error.{event.event_type}", {"event": event, "error": e}
            )

            # Convert to HubError if needed
            if not isinstance(e, HubError):
                raise HubError(
                    f"Failed to handle Hub event: {str(e)}",
                    details={
                        "event_type": event.event_type,
                        "hub_name": event.hub_name,
                        "operation": event.operation,
                    },
                ) from e
            raise

    async def _handle_lifecycle_event(self, event: HubLifecycleEvent) -> None:
        """Handle Hub lifecycle events.

        Args:
            event: Lifecycle event to handle
        """
        # Trigger pre-lifecycle hooks
        self._hook_manager.trigger(
            f"hub.lifecycle.{event.operation}", {"event": event, "state": event.state}
        )

        # Log lifecycle event
        logger.info(
            "Hub lifecycle event",
            extra={
                "hub_name": event.hub_name,
                "operation": event.operation,
                "state": event.state,
                "config": event.config.dict(),
                "event_type": event.event_type,
            },
        )

        if self._lifecycle_counter is not None:
            self._lifecycle_counter.record(1)

        # Trigger post-lifecycle hooks
        self._hook_manager.trigger(
            f"hub.lifecycle.{event.operation}.complete",
            {"event": event, "state": event.state},
        )

    async def _handle_artifact_event(self, event: HubArtifactEvent) -> None:
        """Handle Hub artifact events.

        Args:
            event: Artifact event to handle
        """
        # Trigger pre-artifact hooks
        self._hook_manager.trigger(
            f"hub.artifact.{event.operation}",
            {
                "event": event,
                "artifact_id": event.artifact_id,
                "artifact_type": event.artifact_type,
            },
        )

        # Log artifact event
        logger.info(
            "Hub artifact event",
            extra={
                "hub_name": event.hub_name,
                "operation": event.operation,
                "artifact_id": str(event.artifact_id),
                "artifact_type": event.artifact_type,
                "version": event.version,
                "visibility": event.visibility,
                "event_type": event.event_type,
            },
        )

        if self._artifact_counter is not None:
            self._artifact_counter.record(1)

        # Trigger post-artifact hooks
        self._hook_manager.trigger(
            f"hub.artifact.{event.operation}.complete",
            {
                "event": event,
                "artifact_id": event.artifact_id,
                "artifact_type": event.artifact_type,
            },
        )
