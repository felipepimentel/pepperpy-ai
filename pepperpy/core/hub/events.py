"""Hub events module.

This module defines events specific to the Hub system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from pepperpy.core.events import Event, EventHandler
from pepperpy.hub.base import HubType
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


@dataclass
class HubLifecycleEvent(Event):
    """Event emitted when a Hub's lifecycle state changes.

    Attributes:
        hub_name: Name of the Hub
        hub_type: Type of the Hub
        state: New lifecycle state
        timestamp: When the event occurred
    """

    hub_name: str
    hub_type: HubType
    state: str
    timestamp: datetime = datetime.utcnow()

    def __str__(self) -> str:
        return f"Hub {self.hub_name} ({self.hub_type}) -> {self.state}"


@dataclass
class HubArtifactEvent(Event):
    """Event emitted when a Hub artifact is modified.

    Attributes:
        hub_name: Name of the Hub
        artifact_id: ID of the artifact
        artifact_type: Type of the artifact
        action: Action performed (created, updated, deleted)
        metadata: Additional metadata about the artifact
        timestamp: When the event occurred
    """

    hub_name: str
    artifact_id: str
    artifact_type: str
    action: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

    def __str__(self) -> str:
        return f"Hub {self.hub_name} artifact {self.artifact_id} {self.action}"


class HubEventHandler(EventHandler):
    """Handler for Hub-specific events.

    This handler processes:
    - Hub lifecycle events (initialization, cleanup)
    - Artifact events (creation, updates, deletion)
    """

    async def handle_event(self, event: Event) -> None:
        """Handle a Hub event.

        Args:
            event: Event to handle
        """
        try:
            if isinstance(event, HubLifecycleEvent):
                await self._handle_lifecycle_event(event)
            elif isinstance(event, HubArtifactEvent):
                await self._handle_artifact_event(event)

        except Exception as e:
            logger.error(f"Failed to handle hub event: {e}", exc_info=True)

    async def _handle_lifecycle_event(self, event: HubLifecycleEvent) -> None:
        """Handle a Hub lifecycle event.

        Args:
            event: Lifecycle event to handle
        """
        try:
            logger.info(
                "Hub lifecycle event",
                extra={
                    "hub_name": event.hub_name,
                    "hub_type": event.hub_type,
                    "state": event.state,
                    "timestamp": event.timestamp.isoformat(),
                },
            )

            # Additional lifecycle handling...

        except Exception as e:
            logger.error(f"Failed to handle lifecycle event: {e}", exc_info=True)

    async def _handle_artifact_event(self, event: HubArtifactEvent) -> None:
        """Handle a Hub artifact event.

        Args:
            event: Artifact event to handle
        """
        try:
            logger.info(
                "Hub artifact event",
                extra={
                    "hub_name": event.hub_name,
                    "artifact_id": event.artifact_id,
                    "artifact_type": event.artifact_type,
                    "action": event.action,
                    "metadata": event.metadata,
                    "timestamp": event.timestamp.isoformat(),
                },
            )

            # Additional artifact handling...

        except Exception as e:
            logger.error(f"Failed to handle artifact event: {e}", exc_info=True)
