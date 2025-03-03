"""Workflow scheduler module for the Pepperpy framework.

This module provides the workflow scheduler that manages workflow scheduling and execution.
It handles workflow timing, retries, and error handling.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

from pepperpy.core.base import ComponentBase, ComponentConfig
from pepperpy.core.errors import WorkflowError
from pepperpy.core.types import WorkflowID
from pepperpy.monitoring.metrics import Counter, Histogram
from pepperpy.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Workflow retry policy."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: float = 0.1


@dataclass
class ScheduledWorkflow:
    """Scheduled workflow information."""

    workflow_id: WorkflowID
    workflow: BaseWorkflow
    schedule_time: datetime
    retry_count: int = 0
    last_error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowSchedulerConfig(ComponentConfig):
    """Workflow scheduler configuration."""

    max_concurrent_workflows: int = 10
    scheduler_interval: float = 1.0
    default_retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    workflow_timeout: float = 3600.0


class WorkflowScheduler(ComponentBase):
    """Workflow scheduler for managing workflow execution.

    This class provides functionality for:
    - Workflow scheduling and timing
    - Retry handling and backoff
    - Error handling and recovery
    - Execution monitoring and metrics
    """

    def __init__(
        self,
        config: Optional[WorkflowSchedulerConfig] = None,
    ) -> None:
        """Initialize workflow scheduler.

        Args:
            config: Optional scheduler configuration

        """
        super().__init__(
            config or WorkflowSchedulerConfig(name=self.__class__.__name__),
        )
        self._scheduled_workflows: Dict[WorkflowID, ScheduledWorkflow] = {}
        self._active_workflows: Set[WorkflowID] = set()
        self._scheduler_task: Optional[asyncio.Task[None]] = None

    async def _initialize(self) -> None:
        """Initialize workflow scheduler."""
        try:
            # Initialize metrics
            workflow_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_workflows_total",
                description="Total number of scheduled workflows",
                labels={"status": "scheduled"},
            )
            workflow_execution_time = await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_execution_seconds",
                description="Workflow execution time in seconds",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            )
            workflow_retry_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_retries_total",
                description="Total number of workflow retries",
                labels={"status": "retry"},
            )
            workflow_error_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_errors_total",
                description="Total number of workflow errors",
                labels={"status": "error"},
            )

            self._metrics.update(
                {
                    "workflow_count": workflow_count,
                    "workflow_execution_time": workflow_execution_time,
                    "workflow_retry_count": workflow_retry_count,
                    "workflow_error_count": workflow_error_count,
                },
            )

            # Start scheduler
            if isinstance(self.config, WorkflowSchedulerConfig):
                self._scheduler_task = asyncio.create_task(self._run_scheduler())

            logger.info("Workflow scheduler initialized")

        except Exception as e:
            logger.error("Failed to initialize workflow scheduler: %s", str(e))
            raise WorkflowError(f"Failed to initialize workflow scheduler: {e}") from e

    async def _cleanup(self) -> None:
        """Clean up workflow scheduler resources."""
        try:
            # Stop scheduler
            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass

            # Clear registries
            self._scheduled_workflows.clear()
            self._active_workflows.clear()

            logger.info("Workflow scheduler cleaned up")

        except Exception as e:
            logger.error("Failed to clean up workflow scheduler: %s", str(e))
            raise WorkflowError(f"Failed to clean up workflow scheduler: {e}") from e

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute workflow scheduler functionality.

        This method is not used directly but is required by ComponentBase.
        """

    async def schedule_workflow(
        self,
        workflow: BaseWorkflow,
        schedule_time: Optional[datetime] = None,
        retry_policy: Optional[RetryPolicy] = None,
        **kwargs: Any,
    ) -> None:
        """Schedule a workflow for execution.

        Args:
            workflow: Workflow to schedule
            schedule_time: Optional time to schedule execution
            retry_policy: Optional retry policy
            **kwargs: Additional scheduling parameters

        Raises:
            ValueError: If workflow is already scheduled
            WorkflowError: If scheduling fails

        """
        if workflow.id in self._scheduled_workflows:
            raise ValueError(f"Workflow already scheduled: {workflow.id}")

        if isinstance(self.config, WorkflowSchedulerConfig):
            if len(self._scheduled_workflows) >= self.config.max_concurrent_workflows:
                raise WorkflowError("Maximum concurrent workflows reached")

        try:
            # Create scheduled workflow
            scheduled = ScheduledWorkflow(
                workflow_id=workflow.id,
                workflow=workflow,
                schedule_time=schedule_time or datetime.utcnow(),
                metadata=kwargs,
            )
            self._scheduled_workflows[workflow.id] = scheduled

            # Update metrics
            if isinstance(self._metrics["workflow_count"], Counter):
                await self._metrics["workflow_count"].inc()

            logger.info(
                "Scheduled workflow: %s (time: %s)",
                str(workflow.id),
                scheduled.schedule_time.isoformat(),
            )

        except Exception as e:
            logger.error(
                "Failed to schedule workflow: %s (error: %s)",
                str(workflow.id),
                str(e),
            )
            raise WorkflowError(f"Failed to schedule workflow: {e}") from e

    async def cancel_workflow(
        self,
        workflow_id: Union[UUID, str],
    ) -> None:
        """Cancel a scheduled workflow.

        Args:
            workflow_id: ID of workflow to cancel

        Raises:
            ValueError: If workflow is not scheduled
            WorkflowError: If cancellation fails

        """
        workflow_id = WorkflowID(UUID(str(workflow_id)))
        if workflow_id not in self._scheduled_workflows:
            raise ValueError(f"Workflow not scheduled: {workflow_id}")

        try:
            # Remove workflow
            self._scheduled_workflows.pop(workflow_id)
            self._active_workflows.discard(workflow_id)

            # Update metrics
            if isinstance(self._metrics["workflow_count"], Counter):
                await self._metrics["workflow_count"].inc(-1)

            logger.info("Cancelled workflow: %s", str(workflow_id))

        except Exception as e:
            logger.error(
                "Failed to cancel workflow: %s (error: %s)",
                str(workflow_id),
                str(e),
            )
            raise WorkflowError(f"Failed to cancel workflow: {e}") from e

    def list_scheduled_workflows(self) -> List[Dict[str, Any]]:
        """List scheduled workflows.

        Returns:
            List of scheduled workflow information

        """
        result = []
        for workflow_id, scheduled in self._scheduled_workflows.items():
            result.append(
                {
                    "id": str(workflow_id),
                    "schedule_time": scheduled.schedule_time.isoformat(),
                    "retry_count": scheduled.retry_count,
                    "active": workflow_id in self._active_workflows,
                    "error": (
                        str(scheduled.last_error) if scheduled.last_error else None
                    ),
                },
            )
        return result

    async def _run_scheduler(self) -> None:
        """Run workflow scheduler loop."""
        if not isinstance(self.config, WorkflowSchedulerConfig):
            return

        while True:
            try:
                # Check for workflows to execute
                now = datetime.utcnow()
                for _workflow_id, scheduled in list(self._scheduled_workflows.items()):
                    if scheduled.schedule_time <= now:
                        # Execute workflow
                        await self._execute_workflow(scheduled)

                # Wait for next interval
                await asyncio.sleep(self.config.scheduler_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue running
                error_counter = await self._metrics_manager.create_counter(
                    name=f"{self.config.name}_scheduler_errors_total",
                    description="Total number of scheduler errors",
                    labels={"error": str(e)},
                )
                if isinstance(error_counter, Counter):
                    await error_counter.inc()
                await asyncio.sleep(1.0)  # Back off on error

    async def _execute_workflow(self, scheduled: ScheduledWorkflow) -> None:
        """Execute a scheduled workflow.

        Args:
            scheduled: Scheduled workflow to execute

        """
        workflow_id = scheduled.workflow_id
        if workflow_id in self._active_workflows:
            return

        try:
            # Mark workflow as active
            self._active_workflows.add(workflow_id)
            start_time = datetime.utcnow()

            # Execute workflow
            await scheduled.workflow.execute(**scheduled.metadata)

            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            if isinstance(self._metrics["workflow_execution_time"], Histogram):
                await self._metrics["workflow_execution_time"].observe(duration)

            # Remove workflow if successful
            self._scheduled_workflows.pop(workflow_id)
            self._active_workflows.discard(workflow_id)
            if isinstance(self._metrics["workflow_count"], Counter):
                await self._metrics["workflow_count"].inc(-1)

            logger.info("Executed workflow: %s", str(workflow_id))

        except Exception as e:
            # Handle error
            scheduled.last_error = e
            scheduled.retry_count += 1

            # Update metrics
            if isinstance(self._metrics["workflow_error_count"], Counter):
                await self._metrics["workflow_error_count"].inc()

            # Check retry policy
            if isinstance(self.config, WorkflowSchedulerConfig):
                policy = self.config.default_retry_policy
                if scheduled.retry_count <= policy.max_retries:
                    # Calculate next retry time
                    delay = min(
                        policy.initial_delay
                        * (policy.backoff_factor ** (scheduled.retry_count - 1)),
                        policy.max_delay,
                    )
                    jitter = delay * policy.jitter * (2 * random.random() - 1)
                    scheduled.schedule_time = datetime.utcnow() + timedelta(
                        seconds=delay + jitter,
                    )

                    # Update metrics
                    if isinstance(self._metrics["workflow_retry_count"], Counter):
                        await self._metrics["workflow_retry_count"].inc()

                    logger.warning(
                        "Retrying workflow: %s (attempt: %d, delay: %.2f)",
                        str(workflow_id),
                        scheduled.retry_count,
                        delay,
                    )
                else:
                    # Remove workflow if max retries reached
                    self._scheduled_workflows.pop(workflow_id)
                    if isinstance(self._metrics["workflow_count"], Counter):
                        await self._metrics["workflow_count"].inc(-1)

                    logger.error(
                        "Max retries reached for workflow: %s (error: %s)",
                        str(workflow_id),
                        str(e),
                    )

            self._active_workflows.discard(workflow_id)
