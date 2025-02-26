"""Hub event handlers and types.

This module provides event handling for hub-related events:
- Asset creation/deletion
- Asset updates
- Asset synchronization
- Lifecycle events
- Artifact operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.types import ComponentState
from pepperpy.events.base import Event, EventHandler, EventPriority, EventType
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
    """Base class for hub events."""

    def __init__(
        self,
        event_type: EventType,
        hub_name: str,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize hub event."""
        event_metadata = HubEventMetadata(
            operation=operation,
            details=metadata or {},
        )
        super().__init__(
            event_type=event_type,
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


class HubAssetEvent(HubEvent):
    """Base class for hub asset events."""

    asset_id: UUID = Field(..., description="ID of the asset")
    asset_type: str = Field(..., description="Type of asset")
    asset_name: str = Field(..., description="Name of the asset")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")

    def __init__(
        self,
        event_type: EventType,
        priority: EventPriority,
        hub_name: str,
        operation: str,
        asset_id: UUID,
        asset_type: str,
        asset_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize hub asset event."""
        super().__init__(
            event_type=event_type,
            hub_name=hub_name,
            operation=operation,
            metadata=metadata,
        )
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.asset_name = asset_name


class HubAssetCreatedEvent(HubAssetEvent):
    """Event emitted when a hub asset is created."""

    def __init__(
        self,
        hub_name: str,
        asset_id: UUID,
        asset_type: str,
        asset_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize hub asset created event."""
        super().__init__(
            event_type=EventType.HUB_ASSET_CREATED,
            priority=EventPriority.NORMAL,
            hub_name=hub_name,
            operation="create",
            asset_id=asset_id,
            asset_type=asset_type,
            asset_name=asset_name,
            metadata=metadata,
        )


class HubAssetUpdatedEvent(HubAssetEvent):
    """Event emitted when a hub asset is updated."""

    def __init__(
        self,
        hub_name: str,
        asset_id: UUID,
        asset_type: str,
        asset_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize hub asset updated event."""
        super().__init__(
            event_type=EventType.HUB_ASSET_UPDATED,
            priority=EventPriority.NORMAL,
            hub_name=hub_name,
            operation="update",
            asset_id=asset_id,
            asset_type=asset_type,
            asset_name=asset_name,
            metadata=metadata,
        )


class HubAssetDeletedEvent(HubAssetEvent):
    """Event emitted when a hub asset is deleted."""

    def __init__(
        self,
        hub_name: str,
        asset_id: UUID,
        asset_type: str,
        asset_name: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize hub asset deleted event."""
        super().__init__(
            event_type=EventType.HUB_ASSET_DELETED,
            priority=EventPriority.NORMAL,
            hub_name=hub_name,
            operation="delete",
            asset_id=asset_id,
            asset_type=asset_type,
            asset_name=asset_name,
            metadata=metadata,
        )


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
        # Map operation to event type
        event_type = {
            "create": EventType.HUB_ASSET_CREATED,
            "update": EventType.HUB_ASSET_UPDATED,
            "delete": EventType.HUB_ASSET_DELETED,
        }.get(operation, EventType.HUB_ASSET_CREATED)

        super().__init__(
            event_type=event_type,
            hub_name=hub_name,
            operation=operation,
            metadata=metadata,
        )
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.version = version
        self.visibility = visibility


class HubEventHandler(EventHandler):
    """Handler for hub events."""

    def __init__(self) -> None:
        """Initialize the event handler."""
        super().__init__()
        self._events_counter = None
        self._errors_counter = None
        self._lifecycle_counter = None
        self._artifact_counter = None
        self._asset_counter = None
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
        self._asset_counter = await metrics_manager.create_counter(
            "hub_asset_events_total",
            "Total number of Hub asset events",
            labels={"type": "hub"},
        )

    @property
    def supported_event_types(self) -> List[str]:
        """Get supported event types.

        Returns:
            List of supported event types
        """
        return [
            str(EventType.HUB_ASSET_CREATED),
            str(EventType.HUB_ASSET_UPDATED),
            str(EventType.HUB_ASSET_DELETED),
            str(EventType.COMPONENT_CREATED),
        ]

    async def handle_event(self, event: Event) -> None:
        """Handle hub events.

        Args:
            event: Hub event to handle

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

            # Route event to appropriate handler
            if isinstance(event, HubLifecycleEvent):
                await self._handle_lifecycle_event(event)
            elif isinstance(event, HubArtifactEvent):
                await self._handle_artifact_event(event)
            elif isinstance(event, HubAssetEvent):
                await self._handle_asset_event(event)
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
        try:
            # Trigger pre-lifecycle hooks
            self._hook_manager.trigger(
                f"hub.lifecycle.{event.operation}",
                {"event": event, "state": event.state},
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

        except Exception as e:
            logger.error(
                "Error handling lifecycle event",
                extra={
                    "error": str(e),
                    "hub_name": event.hub_name,
                    "operation": event.operation,
                    "state": event.state,
                },
                exc_info=True,
            )
            raise HubError(
                f"Failed to handle lifecycle event: {str(e)}",
                details={
                    "hub_name": event.hub_name,
                    "operation": event.operation,
                    "state": event.state,
                },
            ) from e

    async def _handle_artifact_event(self, event: HubArtifactEvent) -> None:
        """Handle Hub artifact events.

        Args:
            event: Artifact event to handle
        """
        try:
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

        except Exception as e:
            logger.error(
                "Error handling artifact event",
                extra={
                    "error": str(e),
                    "hub_name": event.hub_name,
                    "operation": event.operation,
                    "artifact_id": str(event.artifact_id),
                    "artifact_type": event.artifact_type,
                },
                exc_info=True,
            )
            raise HubError(
                f"Failed to handle artifact event: {str(e)}",
                details={
                    "artifact_id": str(event.artifact_id),
                    "operation": event.operation,
                    "artifact_type": event.artifact_type,
                },
            ) from e

    async def _handle_asset_event(self, event: HubAssetEvent) -> None:
        """Handle hub asset events.

        Args:
            event: Hub asset event to handle
        """
        try:
            # Trigger pre-asset hooks
            self._hook_manager.trigger(
                f"hub.asset.{event.operation}",
                {
                    "event": event,
                    "asset_id": event.asset_id,
                    "asset_type": event.asset_type,
                },
            )

            # Log asset event
            logger.info(
                f"Hub asset {event.operation}d",
                extra={
                    "hub_name": event.hub_name,
                    "operation": event.operation,
                    "asset_id": str(event.asset_id),
                    "asset_type": event.asset_type,
                    "asset_name": event.asset_name,
                    "event_type": event.event_type,
                },
            )

            # Record metric
            if self._asset_counter is not None:
                self._asset_counter.record(1)

            # Trigger post-asset hooks
            self._hook_manager.trigger(
                f"hub.asset.{event.operation}.complete",
                {
                    "event": event,
                    "asset_id": event.asset_id,
                    "asset_type": event.asset_type,
                },
            )

        except Exception as e:
            logger.error(
                "Error handling asset event",
                extra={
                    "error": str(e),
                    "hub_name": event.hub_name,
                    "operation": event.operation,
                    "asset_id": str(event.asset_id),
                },
                exc_info=True,
            )
            raise HubError(
                f"Failed to handle asset event: {str(e)}",
                details={
                    "asset_id": str(event.asset_id),
                    "operation": event.operation,
                },
            ) from e
