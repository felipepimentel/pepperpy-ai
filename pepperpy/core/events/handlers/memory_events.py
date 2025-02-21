"""Memory event handlers.

This module provides event handlers for memory-related events:
- Memory store events
- Memory retrieve events
- Memory update events
- Memory delete events
"""

import logging
from typing import Dict

from pepperpy.core.events.base import Event, EventHandler
from pepperpy.monitoring import metrics

logger = logging.getLogger(__name__)


class MemoryEventHandler(EventHandler):
    """Handles memory-related events."""

    def __init__(self) -> None:
        """Initialize memory event handler."""
        self._metrics = metrics.MetricsManager.get_instance()
        self._memory_counters: Dict[str, metrics.Counter] = {}

    async def _ensure_counter(
        self, event_type: str, memory_type: str, status: str
    ) -> metrics.Counter:
        """Ensure counter exists for the given parameters.

        Args:
            event_type: Type of event
            memory_type: Type of memory
            status: Event status

        Returns:
            Counter for the given parameters
        """
        counter_key = f"{event_type}_{memory_type}_{status}"
        if counter_key not in self._memory_counters:
            self._memory_counters[counter_key] = await self._metrics.create_counter(
                f"memory_events_total_{counter_key}",
                "Total number of memory events",
                labels={
                    "event_type": event_type,
                    "memory_type": memory_type,
                    "status": status,
                },
            )
        return self._memory_counters[counter_key]

    async def handle(self, event: Event) -> None:
        """Handle memory event.

        Args:
            event: Memory event to handle
        """
        try:
            # Extract memory type from event data
            memory_type = event.data.get("memory_type", "unknown")

            # Handle different event types
            if event.event_type == "memory.store":
                await self._handle_memory_store(memory_type, event.data)
            elif event.event_type == "memory.retrieve":
                await self._handle_memory_retrieve(memory_type, event.data)
            elif event.event_type == "memory.update":
                await self._handle_memory_update(memory_type, event.data)
            elif event.event_type == "memory.delete":
                await self._handle_memory_delete(memory_type, event.data)
            else:
                logger.warning(f"Unknown memory event type: {event.event_type}")

            # Record event metrics
            counter = await self._ensure_counter(
                event.event_type, memory_type, "success"
            )
            counter.record(1)

        except Exception as e:
            # Record failure metrics
            counter = await self._ensure_counter(
                event.event_type,
                event.data.get("memory_type", "unknown"),
                "failure",
            )
            counter.record(1)
            logger.error(
                "Failed to handle memory event",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                },
            )
            raise

    async def _handle_memory_store(self, memory_type: str, data: Dict) -> None:
        """Handle memory store event.

        Args:
            memory_type: Type of memory being stored
            data: Event data
        """
        logger.info(
            f"Memory stored: {memory_type}",
            extra={
                "memory_type": memory_type,
                "key": data.get("key"),
                "metadata": data.get("metadata"),
            },
        )

    async def _handle_memory_retrieve(self, memory_type: str, data: Dict) -> None:
        """Handle memory retrieve event.

        Args:
            memory_type: Type of memory being retrieved
            data: Event data
        """
        logger.info(
            f"Memory retrieved: {memory_type}",
            extra={
                "memory_type": memory_type,
                "key": data.get("key"),
                "query": data.get("query"),
            },
        )

    async def _handle_memory_update(self, memory_type: str, data: Dict) -> None:
        """Handle memory update event.

        Args:
            memory_type: Type of memory being updated
            data: Event data
        """
        logger.info(
            f"Memory updated: {memory_type}",
            extra={
                "memory_type": memory_type,
                "key": data.get("key"),
                "metadata": data.get("metadata"),
            },
        )

    async def _handle_memory_delete(self, memory_type: str, data: Dict) -> None:
        """Handle memory delete event.

        Args:
            memory_type: Type of memory being deleted
            data: Event data
        """
        logger.info(
            f"Memory deleted: {memory_type}",
            extra={
                "memory_type": memory_type,
                "key": data.get("key"),
            },
        )
