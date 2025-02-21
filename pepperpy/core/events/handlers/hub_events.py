"""Hub event handlers.

This module provides event handlers for hub-related events:
- Hub asset events (prompts, agents, workflows)
- Hub sync events
- Hub validation events
"""

import logging
from typing import Dict

from pepperpy.core.events.base import Event, EventHandler
from pepperpy.monitoring import metrics

logger = logging.getLogger(__name__)


class HubEventHandler(EventHandler):
    """Handles hub-related events."""

    def __init__(self) -> None:
        """Initialize hub event handler."""
        self._metrics = metrics.MetricsManager.get_instance()
        self._hub_counters: Dict[str, metrics.Counter] = {}

    async def _ensure_counter(
        self, event_type: str, asset_type: str, status: str
    ) -> metrics.Counter:
        """Ensure counter exists for the given parameters.

        Args:
            event_type: Type of event
            asset_type: Type of asset
            status: Event status

        Returns:
            Counter for the given parameters
        """
        counter_key = f"{event_type}_{asset_type}_{status}"
        if counter_key not in self._hub_counters:
            self._hub_counters[counter_key] = await self._metrics.create_counter(
                f"hub_events_total_{counter_key}",
                "Total number of hub events",
                labels={
                    "event_type": event_type,
                    "asset_type": asset_type,
                    "status": status,
                },
            )
        return self._hub_counters[counter_key]

    async def handle(self, event: Event) -> None:
        """Handle hub event.

        Args:
            event: Hub event to handle
        """
        try:
            # Extract asset type from event data
            asset_type = event.data.get("asset_type", "unknown")

            # Handle different event types
            if event.event_type == "hub.asset.created":
                await self._handle_asset_created(asset_type, event.data)
            elif event.event_type == "hub.asset.updated":
                await self._handle_asset_updated(asset_type, event.data)
            elif event.event_type == "hub.asset.deleted":
                await self._handle_asset_deleted(asset_type, event.data)
            elif event.event_type == "hub.sync.started":
                await self._handle_sync_started(event.data)
            elif event.event_type == "hub.sync.completed":
                await self._handle_sync_completed(event.data)
            elif event.event_type == "hub.sync.failed":
                await self._handle_sync_failed(event.data)
            elif event.event_type == "hub.validation.success":
                await self._handle_validation_success(asset_type, event.data)
            elif event.event_type == "hub.validation.failure":
                await self._handle_validation_failure(asset_type, event.data)
            else:
                logger.warning(f"Unknown hub event type: {event.event_type}")

            # Record event metrics
            counter = await self._ensure_counter(
                event.event_type, asset_type, "success"
            )
            counter.record(1)

        except Exception as e:
            # Record failure metrics
            counter = await self._ensure_counter(
                event.event_type,
                event.data.get("asset_type", "unknown"),
                "failure",
            )
            counter.record(1)
            logger.error(
                "Failed to handle hub event",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                },
            )
            raise

    async def _handle_asset_created(self, asset_type: str, data: Dict) -> None:
        """Handle asset created event.

        Args:
            asset_type: Type of asset created
            data: Event data
        """
        logger.info(
            f"Hub asset created: {asset_type}",
            extra={
                "asset_type": asset_type,
                "asset_id": data.get("asset_id"),
                "metadata": data.get("metadata"),
            },
        )

    async def _handle_asset_updated(self, asset_type: str, data: Dict) -> None:
        """Handle asset updated event.

        Args:
            asset_type: Type of asset updated
            data: Event data
        """
        logger.info(
            f"Hub asset updated: {asset_type}",
            extra={
                "asset_type": asset_type,
                "asset_id": data.get("asset_id"),
                "metadata": data.get("metadata"),
            },
        )

    async def _handle_asset_deleted(self, asset_type: str, data: Dict) -> None:
        """Handle asset deleted event.

        Args:
            asset_type: Type of asset deleted
            data: Event data
        """
        logger.info(
            f"Hub asset deleted: {asset_type}",
            extra={
                "asset_type": asset_type,
                "asset_id": data.get("asset_id"),
            },
        )

    async def _handle_sync_started(self, data: Dict) -> None:
        """Handle sync started event.

        Args:
            data: Event data
        """
        logger.info(
            "Hub sync started",
            extra={
                "sync_id": data.get("sync_id"),
                "source": data.get("source"),
            },
        )

    async def _handle_sync_completed(self, data: Dict) -> None:
        """Handle sync completed event.

        Args:
            data: Event data
        """
        logger.info(
            "Hub sync completed",
            extra={
                "sync_id": data.get("sync_id"),
                "stats": data.get("stats"),
            },
        )

    async def _handle_sync_failed(self, data: Dict) -> None:
        """Handle sync failed event.

        Args:
            data: Event data
        """
        logger.error(
            "Hub sync failed",
            extra={
                "sync_id": data.get("sync_id"),
                "error": data.get("error"),
            },
        )

    async def _handle_validation_success(self, asset_type: str, data: Dict) -> None:
        """Handle validation success event.

        Args:
            asset_type: Type of asset validated
            data: Event data
        """
        logger.info(
            f"Hub validation succeeded: {asset_type}",
            extra={
                "asset_type": asset_type,
                "asset_id": data.get("asset_id"),
                "validation_type": data.get("validation_type"),
            },
        )

    async def _handle_validation_failure(self, asset_type: str, data: Dict) -> None:
        """Handle validation failure event.

        Args:
            asset_type: Type of asset validated
            data: Event data
        """
        logger.error(
            f"Hub validation failed: {asset_type}",
            extra={
                "asset_type": asset_type,
                "asset_id": data.get("asset_id"),
                "validation_type": data.get("validation_type"),
                "errors": data.get("errors"),
            },
        )
