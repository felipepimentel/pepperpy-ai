"""Agent event handlers.

This module provides event handlers for agent-related events:
- Agent lifecycle events
- Agent task events
- Agent state events
"""

import logging
from typing import Dict

from pepperpy.core.events.base import Event, EventHandler
from pepperpy.monitoring import metrics

logger = logging.getLogger(__name__)


class AgentEventHandler(EventHandler):
    """Handles agent-related events."""

    def __init__(self) -> None:
        """Initialize agent event handler."""
        self._metrics = metrics.MetricsManager.get_instance()
        self._agent_counters: Dict[str, metrics.Counter] = {}

    async def _ensure_counter(
        self, event_type: str, agent_id: str, status: str
    ) -> metrics.Counter:
        """Ensure counter exists for the given parameters.

        Args:
            event_type: Type of event
            agent_id: ID of the agent
            status: Event status

        Returns:
            Counter for the given parameters
        """
        counter_key = f"{event_type}_{agent_id}_{status}"
        if counter_key not in self._agent_counters:
            self._agent_counters[counter_key] = await self._metrics.create_counter(
                f"agent_events_total_{counter_key}",
                "Total number of agent events",
                labels={
                    "event_type": event_type,
                    "agent_id": agent_id,
                    "status": status,
                },
            )
        return self._agent_counters[counter_key]

    async def handle(self, event: Event) -> None:
        """Handle agent event.

        Args:
            event: Agent event to handle
        """
        try:
            # Extract agent ID from event data
            agent_id = event.data.get("agent_id", "unknown")

            # Handle different event types
            if event.event_type == "agent.started":
                await self._handle_agent_started(agent_id, event.data)
            elif event.event_type == "agent.stopped":
                await self._handle_agent_stopped(agent_id, event.data)
            elif event.event_type == "agent.task.started":
                await self._handle_task_started(agent_id, event.data)
            elif event.event_type == "agent.task.completed":
                await self._handle_task_completed(agent_id, event.data)
            elif event.event_type == "agent.task.failed":
                await self._handle_task_failed(agent_id, event.data)
            elif event.event_type == "agent.state.changed":
                await self._handle_state_changed(agent_id, event.data)
            else:
                logger.warning(f"Unknown agent event type: {event.event_type}")

            # Record event metrics
            counter = await self._ensure_counter(event.event_type, agent_id, "success")
            counter.record(1)

        except Exception as e:
            # Record failure metrics
            counter = await self._ensure_counter(
                event.event_type,
                event.data.get("agent_id", "unknown"),
                "failure",
            )
            counter.record(1)
            logger.error(
                "Failed to handle agent event",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                },
            )
            raise

    async def _handle_agent_started(self, agent_id: str, data: Dict) -> None:
        """Handle agent started event.

        Args:
            agent_id: ID of the agent
            data: Event data
        """
        logger.info(
            f"Agent started: {agent_id}",
            extra={
                "agent_id": agent_id,
                "config": data.get("config"),
            },
        )

    async def _handle_agent_stopped(self, agent_id: str, data: Dict) -> None:
        """Handle agent stopped event.

        Args:
            agent_id: ID of the agent
            data: Event data
        """
        logger.info(
            f"Agent stopped: {agent_id}",
            extra={
                "agent_id": agent_id,
                "reason": data.get("reason"),
            },
        )

    async def _handle_task_started(self, agent_id: str, data: Dict) -> None:
        """Handle task started event.

        Args:
            agent_id: ID of the agent
            data: Event data
        """
        logger.info(
            f"Agent task started: {agent_id}",
            extra={
                "agent_id": agent_id,
                "task_id": data.get("task_id"),
                "task_type": data.get("task_type"),
            },
        )

    async def _handle_task_completed(self, agent_id: str, data: Dict) -> None:
        """Handle task completed event.

        Args:
            agent_id: ID of the agent
            data: Event data
        """
        logger.info(
            f"Agent task completed: {agent_id}",
            extra={
                "agent_id": agent_id,
                "task_id": data.get("task_id"),
                "result": data.get("result"),
            },
        )

    async def _handle_task_failed(self, agent_id: str, data: Dict) -> None:
        """Handle task failed event.

        Args:
            agent_id: ID of the agent
            data: Event data
        """
        logger.error(
            f"Agent task failed: {agent_id}",
            extra={
                "agent_id": agent_id,
                "task_id": data.get("task_id"),
                "error": data.get("error"),
            },
        )

    async def _handle_state_changed(self, agent_id: str, data: Dict) -> None:
        """Handle state changed event.

        Args:
            agent_id: ID of the agent
            data: Event data
        """
        logger.info(
            f"Agent state changed: {agent_id}",
            extra={
                "agent_id": agent_id,
                "old_state": data.get("old_state"),
                "new_state": data.get("new_state"),
            },
        )
