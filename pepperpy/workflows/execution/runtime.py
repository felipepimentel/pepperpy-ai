"""Workflow engine module for the Pepperpy framework.

This module provides the workflow engine that manages workflow execution.
It handles workflow lifecycle, scheduling, and monitoring.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type, Union
from uuid import UUID

from pepperpy.core.common.base import ComponentBase, ComponentConfig
from pepperpy.core.errors import StateError, WorkflowError
from pepperpy.core.common.types import WorkflowID
from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
from pepperpy.workflows.base import BaseWorkflow, WorkflowConfig, WorkflowState

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEngineConfig(ComponentConfig):
    """Workflow engine configuration."""

    max_concurrent_workflows: int = 10
    workflow_timeout: float = 3600.0
    scheduler_interval: float = 1.0
    retry_policy: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine(ComponentBase):
    """Workflow engine for managing workflow execution.

    This class provides functionality for:
    - Workflow registration and discovery
    - Workflow lifecycle management
    - Workflow scheduling and execution
    - Workflow monitoring and metrics
    """

    def __init__(
        self,
        config: Optional[WorkflowEngineConfig] = None,
    ) -> None:
        """Initialize workflow engine.

        Args:
            config: Optional engine configuration
        """
        super().__init__(config or WorkflowEngineConfig(name=self.__class__.__name__))
        self._workflows: Dict[WorkflowID, BaseWorkflow] = {}
        self._workflow_types: Dict[str, Type[BaseWorkflow]] = {}
        self._active_workflows: Set[WorkflowID] = set()
        self._scheduled_workflows: Dict[WorkflowID, datetime] = {}
        self._scheduler_task: Optional[asyncio.Task[None]] = None
        self._metrics_manager = MetricsManager.get_instance()
        self._metrics: Dict[str, Union[Counter, Histogram]] = {}

    async def _initialize(self) -> None:
        """Initialize workflow engine."""
        try:
            # Initialize metrics
            workflow_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_workflows_total",
                description="Total number of workflows registered",
                labels={"status": "active"},
            )
            workflow_execution_time = await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_execution_seconds",
                description="Workflow execution time in seconds",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            )
            workflow_queue_time = await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_queue_seconds",
                description="Workflow queue time in seconds",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            )
            workflow_retry_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_retries_total",
                description="Total number of workflow retries",
                labels={"status": "retry"},
            )

            self._metrics.update({
                "workflow_count": workflow_count,
                "workflow_execution_time": workflow_execution_time,
                "workflow_queue_time": workflow_queue_time,
                "workflow_retry_count": workflow_retry_count,
            })

            # Start scheduler
            if isinstance(self.config, WorkflowEngineConfig):
                self._scheduler_task = asyncio.create_task(self._run_scheduler())

            logger.info("Workflow engine initialized")

        except Exception as e:
            logger.error("Failed to initialize workflow engine: %s", str(e))
            raise WorkflowError(f"Failed to initialize workflow engine: {e}")

    async def _cleanup(self) -> None:
        """Clean up workflow engine resources."""
        try:
            # Stop scheduler
            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass

            # Clean up active workflows
            for workflow_id in list(self._active_workflows):
                await self.stop_workflow(workflow_id)

            # Clear registries
            self._workflows.clear()
            self._workflow_types.clear()
            self._active_workflows.clear()
            self._scheduled_workflows.clear()

            logger.info("Workflow engine cleaned up")

        except Exception as e:
            logger.error("Failed to clean up workflow engine: %s", str(e))
            raise WorkflowError(f"Failed to clean up workflow engine: {e}")

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute workflow engine functionality.

        This method is not used directly but is required by ComponentBase.
        """
        pass

    def register_workflow(self, workflow_type: Type[BaseWorkflow]) -> None:
        """Register a workflow type.

        Args:
            workflow_type: Workflow class to register

        Raises:
            ValueError: If workflow type is already registered
        """
        name = workflow_type.__name__
        if name in self._workflow_types:
            raise ValueError(f"Workflow type already registered: {name}")

        self._workflow_types[name] = workflow_type
        logger.info("Registered workflow type: %s", name)

    async def create_workflow(
        self,
        workflow_type: str,
        config: Optional[WorkflowConfig] = None,
        schedule_time: Optional[datetime] = None,
        **kwargs: Any,
    ) -> WorkflowID:
        """Create a new workflow instance.

        Args:
            workflow_type: Type of workflow to create
            config: Optional workflow configuration
            schedule_time: Optional time to schedule workflow execution
            **kwargs: Additional workflow parameters

        Returns:
            ID of created workflow

        Raises:
            ValueError: If workflow type is not registered
            WorkflowError: If workflow creation fails
        """
        if workflow_type not in self._workflow_types:
            raise ValueError(f"Workflow type not registered: {workflow_type}")

        if isinstance(self.config, WorkflowEngineConfig):
            if len(self._workflows) >= self.config.max_concurrent_workflows:
                raise WorkflowError("Maximum concurrent workflows reached")

        try:
            # Create workflow instance
            workflow_cls = self._workflow_types[workflow_type]
            workflow = workflow_cls(config=config, **kwargs)
            workflow_id = workflow.id

            # Initialize workflow
            await workflow.initialize()
            self._workflows[workflow_id] = workflow

            # Update metrics
            if isinstance(self._metrics["workflow_count"], Counter):
                await self._metrics["workflow_count"].inc()

            # Schedule workflow if requested
            if schedule_time:
                self._scheduled_workflows[workflow_id] = schedule_time

            logger.info(
                "Created workflow: %s (type: %s)",
                str(workflow_id),
                workflow_type,
            )
            return workflow_id

        except Exception as e:
            logger.error(
                "Failed to create workflow: %s (type: %s, error: %s)",
                str(workflow_id),
                workflow_type,
                str(e),
            )
            raise WorkflowError(f"Failed to create workflow: {e}") from e

    async def start_workflow(
        self,
        workflow_id: Union[UUID, str],
        **kwargs: Any,
    ) -> None:
        """Start workflow execution.

        Args:
            workflow_id: ID of workflow to start
            **kwargs: Workflow execution parameters

        Raises:
            ValueError: If workflow not found
            StateError: If workflow is not in valid state
            WorkflowError: If workflow execution fails
        """
        workflow_id = WorkflowID(UUID(str(workflow_id)))
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self._workflows[workflow_id]
        if workflow.state != WorkflowState.READY:
            raise StateError(
                f"Workflow not ready: {workflow_id} (state: {workflow.state})"
            )

        try:
            # Start workflow execution
            self._active_workflows.add(workflow_id)
            start_time = datetime.utcnow()

            # Execute workflow
            await workflow.execute(**kwargs)

            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            if isinstance(self._metrics["workflow_execution_time"], Histogram):
                await self._metrics["workflow_execution_time"].observe(duration)

            # Remove from scheduled workflows if present
            self._scheduled_workflows.pop(workflow_id, None)

            logger.info("Started workflow: %s", str(workflow_id))

        except Exception as e:
            logger.error(
                "Failed to start workflow: %s (error: %s)",
                str(workflow_id),
                str(e),
            )
            self._active_workflows.discard(workflow_id)
            raise WorkflowError(f"Failed to start workflow: {e}") from e

    async def stop_workflow(self, workflow_id: Union[UUID, str]) -> None:
        """Stop workflow execution.

        Args:
            workflow_id: ID of workflow to stop

        Raises:
            ValueError: If workflow not found
            WorkflowError: If workflow cleanup fails
        """
        workflow_id = WorkflowID(UUID(str(workflow_id)))
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        try:
            # Clean up workflow
            workflow = self._workflows[workflow_id]
            await workflow.cleanup()

            # Remove workflow
            self._workflows.pop(workflow_id)
            self._active_workflows.discard(workflow_id)
            self._scheduled_workflows.pop(workflow_id, None)

            # Update metrics
            if isinstance(self._metrics["workflow_count"], Counter):
                await self._metrics["workflow_count"].inc(-1)

            logger.info("Stopped workflow: %s", str(workflow_id))

        except Exception as e:
            logger.error(
                "Failed to stop workflow: %s (error: %s)",
                str(workflow_id),
                str(e),
            )
            raise WorkflowError(f"Failed to stop workflow: {e}") from e

    def get_workflow(self, workflow_id: Union[UUID, str]) -> BaseWorkflow:
        """Get workflow instance.

        Args:
            workflow_id: ID of workflow to get

        Returns:
            Workflow instance

        Raises:
            ValueError: If workflow not found
        """
        workflow_id = WorkflowID(UUID(str(workflow_id)))
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        return self._workflows[workflow_id]

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows.

        Returns:
            List of workflow information
        """
        result = []
        for workflow_id, workflow in self._workflows.items():
            result.append({
                "id": str(workflow_id),
                "type": workflow.__class__.__name__,
                "state": workflow.state,
                "active": workflow_id in self._active_workflows,
                "scheduled": workflow_id in self._scheduled_workflows,
            })
        return result

    def list_workflow_types(self) -> List[str]:
        """List registered workflow types.

        Returns:
            List of workflow type names
        """
        return list(self._workflow_types.keys())

    async def _run_scheduler(self) -> None:
        """Run workflow scheduler loop."""
        if not isinstance(self.config, WorkflowEngineConfig):
            return

        while True:
            try:
                # Check for workflows to execute
                now = datetime.utcnow()
                for workflow_id, schedule_time in list(
                    self._scheduled_workflows.items()
                ):
                    if schedule_time <= now:
                        # Start workflow
                        await self.start_workflow(workflow_id)

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
