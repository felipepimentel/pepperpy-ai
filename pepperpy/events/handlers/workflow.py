"""Workflow event handler.

This module provides an event handler for workflow-related events.
"""

from typing import Any

from pepperpy.events.base import Event, EventHandler
from pepperpy.monitoring import logger


class WorkflowEventHandler(EventHandler):
    """Workflow event handler."""

    def __init__(self, name: str) -> None:
        """Initialize workflow event handler.

        Args:
            name: Handler name
        """
        super().__init__(name)
        self._workflows: dict[str, dict[str, Any]] = {}

    async def _handle_event(self, event: Event) -> None:
        """Handle workflow event.

        Args:
            event: Workflow event to handle
        """
        try:
            if event.type == "workflow.started":
                await self._handle_workflow_started(event)
            elif event.type == "workflow.completed":
                await self._handle_workflow_completed(event)
            elif event.type == "workflow.failed":
                await self._handle_workflow_failed(event)
            else:
                logger.warning(f"Unknown workflow event type: {event.type}")

        except Exception as e:
            logger.error(f"Failed to handle workflow event: {e}")
            raise

    async def _handle_workflow_started(self, event: Event) -> None:
        """Handle workflow started event.

        Args:
            event: Workflow started event
        """
        workflow_id = event.data.get("workflow_id")
        if not workflow_id:
            logger.error("Missing workflow ID in workflow started event")
            return

        self._workflows[workflow_id] = {
            "state": "running",
            "metadata": event.metadata,
            **event.data,
        }

        logger.info(f"Workflow started: {workflow_id}")

    async def _handle_workflow_completed(self, event: Event) -> None:
        """Handle workflow completed event.

        Args:
            event: Workflow completed event
        """
        workflow_id = event.data.get("workflow_id")
        if not workflow_id:
            logger.error("Missing workflow ID in workflow completed event")
            return

        if workflow_id in self._workflows:
            self._workflows[workflow_id].update({
                "state": "completed",
                "completed_at": event.timestamp,
                "result": event.data.get("result"),
            })
            logger.info(f"Workflow completed: {workflow_id}")
        else:
            logger.warning(f"Workflow not found: {workflow_id}")

    async def _handle_workflow_failed(self, event: Event) -> None:
        """Handle workflow failed event.

        Args:
            event: Workflow failed event
        """
        workflow_id = event.data.get("workflow_id")
        error = event.data.get("error")

        if not workflow_id:
            logger.error("Missing workflow ID in workflow failed event")
            return

        if workflow_id in self._workflows:
            self._workflows[workflow_id].update({
                "state": "failed",
                "failed_at": event.timestamp,
                "error": error,
            })
            logger.error(f"Workflow failed: {workflow_id} - {error}")
        else:
            logger.warning(f"Workflow not found: {workflow_id}")


# Export public API
__all__ = ["WorkflowEventHandler"]
