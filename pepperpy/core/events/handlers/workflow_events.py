"""Workflow event handlers.

This module provides event handlers for workflow-related events:
- Workflow lifecycle events
- Workflow step events
- Workflow state events
"""

import logging
from typing import Dict

from pepperpy.core.events.base import Event, EventHandler
from pepperpy.monitoring import metrics

logger = logging.getLogger(__name__)


class WorkflowEventHandler(EventHandler):
    """Handles workflow-related events."""

    def __init__(self) -> None:
        """Initialize workflow event handler."""
        self._metrics = metrics.MetricsManager.get_instance()
        self._workflow_counters: Dict[str, metrics.Counter] = {}

    async def _ensure_counter(
        self, event_type: str, workflow_id: str, status: str
    ) -> metrics.Counter:
        """Ensure counter exists for the given parameters.

        Args:
            event_type: Type of event
            workflow_id: ID of the workflow
            status: Event status

        Returns:
            Counter for the given parameters
        """
        counter_key = f"{event_type}_{workflow_id}_{status}"
        if counter_key not in self._workflow_counters:
            self._workflow_counters[counter_key] = await self._metrics.create_counter(
                f"workflow_events_total_{counter_key}",
                "Total number of workflow events",
                labels={
                    "event_type": event_type,
                    "workflow_id": workflow_id,
                    "status": status,
                },
            )
        return self._workflow_counters[counter_key]

    async def handle(self, event: Event) -> None:
        """Handle workflow event.

        Args:
            event: Workflow event to handle
        """
        try:
            # Extract workflow ID from event data
            workflow_id = event.data.get("workflow_id", "unknown")

            # Handle different event types
            if event.event_type == "workflow.started":
                await self._handle_workflow_started(workflow_id, event.data)
            elif event.event_type == "workflow.completed":
                await self._handle_workflow_completed(workflow_id, event.data)
            elif event.event_type == "workflow.failed":
                await self._handle_workflow_failed(workflow_id, event.data)
            elif event.event_type == "workflow.step.started":
                await self._handle_step_started(workflow_id, event.data)
            elif event.event_type == "workflow.step.completed":
                await self._handle_step_completed(workflow_id, event.data)
            elif event.event_type == "workflow.step.failed":
                await self._handle_step_failed(workflow_id, event.data)
            elif event.event_type == "workflow.state.changed":
                await self._handle_state_changed(workflow_id, event.data)
            else:
                logger.warning(f"Unknown workflow event type: {event.event_type}")

            # Record event metrics
            counter = await self._ensure_counter(
                event.event_type, workflow_id, "success"
            )
            counter.record(1)

        except Exception as e:
            # Record failure metrics
            counter = await self._ensure_counter(
                event.event_type,
                event.data.get("workflow_id", "unknown"),
                "failure",
            )
            counter.record(1)
            logger.error(
                "Failed to handle workflow event",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                },
            )
            raise

    async def _handle_workflow_started(self, workflow_id: str, data: Dict) -> None:
        """Handle workflow started event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.info(
            f"Workflow started: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "config": data.get("config"),
            },
        )

    async def _handle_workflow_completed(self, workflow_id: str, data: Dict) -> None:
        """Handle workflow completed event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.info(
            f"Workflow completed: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "result": data.get("result"),
            },
        )

    async def _handle_workflow_failed(self, workflow_id: str, data: Dict) -> None:
        """Handle workflow failed event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.error(
            f"Workflow failed: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "error": data.get("error"),
            },
        )

    async def _handle_step_started(self, workflow_id: str, data: Dict) -> None:
        """Handle step started event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.info(
            f"Workflow step started: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "step_id": data.get("step_id"),
                "step_type": data.get("step_type"),
            },
        )

    async def _handle_step_completed(self, workflow_id: str, data: Dict) -> None:
        """Handle step completed event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.info(
            f"Workflow step completed: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "step_id": data.get("step_id"),
                "result": data.get("result"),
            },
        )

    async def _handle_step_failed(self, workflow_id: str, data: Dict) -> None:
        """Handle step failed event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.error(
            f"Workflow step failed: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "step_id": data.get("step_id"),
                "error": data.get("error"),
            },
        )

    async def _handle_state_changed(self, workflow_id: str, data: Dict) -> None:
        """Handle state changed event.

        Args:
            workflow_id: ID of the workflow
            data: Event data
        """
        logger.info(
            f"Workflow state changed: {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "old_state": data.get("old_state"),
                "new_state": data.get("new_state"),
            },
        )
