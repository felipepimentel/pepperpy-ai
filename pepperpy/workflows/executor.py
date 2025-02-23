"""Workflow executor module for the Pepperpy framework.

This module provides the workflow executor that manages workflow execution.
It handles workflow steps, dependencies, and monitoring.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from pepperpy.core.base import ComponentBase, ComponentConfig
from pepperpy.core.errors import StateError, WorkflowError
from pepperpy.core.types import WorkflowID
from pepperpy.monitoring.metrics import Counter, Histogram
from pepperpy.workflows.base import BaseWorkflow, WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Workflow execution context."""

    workflow_id: WorkflowID
    workflow: BaseWorkflow
    current_step: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutorConfig(ComponentConfig):
    """Workflow executor configuration."""

    max_concurrent_steps: int = 5
    step_timeout: float = 300.0
    execution_timeout: float = 3600.0
    monitor_interval: float = 1.0


class WorkflowExecutor(ComponentBase):
    """Workflow executor for managing workflow execution.

    This class provides functionality for:
    - Step execution and sequencing
    - Dependency management
    - Execution monitoring
    - Resource management
    """

    def __init__(
        self,
        config: Optional[WorkflowExecutorConfig] = None,
    ) -> None:
        """Initialize workflow executor.

        Args:
            config: Optional executor configuration
        """
        super().__init__(config or WorkflowExecutorConfig(name=self.__class__.__name__))
        self._active_executions: Dict[WorkflowID, ExecutionContext] = {}
        self._active_steps: Set[str] = set()
        self._monitor_task: Optional[asyncio.Task[None]] = None

    async def _initialize(self) -> None:
        """Initialize workflow executor."""
        try:
            # Initialize metrics
            execution_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_executions_total",
                description="Total number of workflow executions",
                labels={"status": "success"},
            )
            execution_time = await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_execution_seconds",
                description="Workflow execution time in seconds",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            )
            step_count = await self._metrics_manager.create_counter(
                name=f"{self.config.name}_steps_total",
                description="Total number of workflow steps executed",
                labels={"status": "success"},
            )
            step_time = await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_step_seconds",
                description="Workflow step execution time in seconds",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )

            self._metrics.update({
                "execution_count": execution_count,
                "execution_time": execution_time,
                "step_count": step_count,
                "step_time": step_time,
            })

            # Start monitor
            if isinstance(self.config, WorkflowExecutorConfig):
                self._monitor_task = asyncio.create_task(self._run_monitor())

            logger.info("Workflow executor initialized")

        except Exception as e:
            logger.error("Failed to initialize workflow executor: %s", str(e))
            raise WorkflowError(f"Failed to initialize workflow executor: {e}")

    async def _cleanup(self) -> None:
        """Clean up workflow executor resources."""
        try:
            # Stop monitor
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

            # Clean up active executions
            for context in list(self._active_executions.values()):
                await self._cleanup_execution(context)

            # Clear registries
            self._active_executions.clear()
            self._active_steps.clear()

            logger.info("Workflow executor cleaned up")

        except Exception as e:
            logger.error("Failed to clean up workflow executor: %s", str(e))
            raise WorkflowError(f"Failed to clean up workflow executor: {e}")

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute workflow executor functionality.

        This method is not used directly but is required by ComponentBase.
        """
        pass

    async def execute_workflow(
        self,
        workflow: BaseWorkflow,
        **kwargs: Any,
    ) -> None:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            **kwargs: Execution parameters

        Raises:
            ValueError: If workflow is already executing
            StateError: If workflow is not in valid state
            WorkflowError: If execution fails
        """
        if workflow.id in self._active_executions:
            raise ValueError(f"Workflow already executing: {workflow.id}")

        if workflow.state != WorkflowState.READY:
            raise StateError(
                f"Workflow not ready: {workflow.id} (state: {workflow.state})"
            )

        try:
            # Create execution context
            context = ExecutionContext(
                workflow_id=workflow.id,
                workflow=workflow,
                metadata=kwargs,
            )
            self._active_executions[workflow.id] = context

            # Execute workflow steps
            for step in workflow.steps:
                await self._execute_step(context, step)

            # Update metrics
            duration = (datetime.utcnow() - context.start_time).total_seconds()
            if isinstance(self._metrics["execution_count"], Counter):
                await self._metrics["execution_count"].inc()
            if isinstance(self._metrics["execution_time"], Histogram):
                await self._metrics["execution_time"].observe(duration)

            logger.info("Executed workflow: %s", str(workflow.id))

        except Exception as e:
            logger.error(
                "Failed to execute workflow: %s (error: %s)",
                str(workflow.id),
                str(e),
            )
            raise WorkflowError(f"Failed to execute workflow: {e}") from e

        finally:
            # Clean up execution
            if workflow.id in self._active_executions:
                await self._cleanup_execution(context)

    async def _execute_step(
        self,
        context: ExecutionContext,
        step: WorkflowStep,
    ) -> None:
        """Execute a workflow step.

        Args:
            context: Execution context
            step: Step to execute

        Raises:
            WorkflowError: If step execution fails
        """
        if isinstance(self.config, WorkflowExecutorConfig):
            if len(self._active_steps) >= self.config.max_concurrent_steps:
                raise WorkflowError("Maximum concurrent steps reached")

        try:
            # Update context
            context.current_step = step.name
            start_time = datetime.utcnow()

            # Execute step
            self._active_steps.add(step.name)
            await context.workflow.execute_step(step)

            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            if isinstance(self._metrics["step_count"], Counter):
                await self._metrics["step_count"].inc()
            if isinstance(self._metrics["step_time"], Histogram):
                await self._metrics["step_time"].observe(duration)

            logger.info(
                "Executed step: %s (workflow: %s)",
                step.name,
                str(context.workflow_id),
            )

        except Exception as e:
            logger.error(
                "Failed to execute step: %s (workflow: %s, error: %s)",
                step.name,
                str(context.workflow_id),
                str(e),
            )
            raise WorkflowError(f"Failed to execute step {step.name}: {e}") from e

        finally:
            # Clean up step
            self._active_steps.discard(step.name)
            context.current_step = None

    async def _cleanup_execution(self, context: ExecutionContext) -> None:
        """Clean up workflow execution.

        Args:
            context: Execution context to clean up
        """
        try:
            # Update context
            context.end_time = datetime.utcnow()
            self._active_executions.pop(context.workflow_id, None)

            # Clean up active steps
            if context.current_step:
                self._active_steps.discard(context.current_step)

        except Exception as e:
            logger.error(
                "Failed to clean up execution: %s (error: %s)",
                str(context.workflow_id),
                str(e),
            )

    async def _run_monitor(self) -> None:
        """Run workflow execution monitor loop."""
        if not isinstance(self.config, WorkflowExecutorConfig):
            return

        while True:
            try:
                # Check for timed out executions
                now = datetime.utcnow()
                timeout = timedelta(seconds=self.config.execution_timeout)

                for context in list(self._active_executions.values()):
                    if now - context.start_time > timeout:
                        # Clean up timed out execution
                        logger.warning(
                            "Execution timed out: %s",
                            str(context.workflow_id),
                        )
                        await self._cleanup_execution(context)

                # Wait for next interval
                await asyncio.sleep(self.config.monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue running
                error_counter = await self._metrics_manager.create_counter(
                    name=f"{self.config.name}_monitor_errors_total",
                    description="Total number of monitor errors",
                    labels={"error": str(e)},
                )
                if isinstance(error_counter, Counter):
                    await error_counter.inc()
                await asyncio.sleep(1.0)  # Back off on error
