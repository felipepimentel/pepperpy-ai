"""Workflow execution engine."""

import asyncio
import logging
from typing import Any, Dict, List, Set

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState

from .base import WorkflowContext, WorkflowState, WorkflowStep
from .errors import (
    StepExecutionError,
    StepTimeoutError,
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowValidationError,
)

logger = logging.getLogger(__name__)


class WorkflowEngine(Lifecycle):
    """Unified workflow execution engine.

    Features:
    - Workflow registration and validation
    - State management and error handling
    - Variable passing between steps
    - Execution history tracking
    - Conditional step execution
    - Retry handling
    - Timeout management
    """

    def __init__(self) -> None:
        """Initialize workflow engine."""
        super().__init__()
        self._workflows: Dict[str, List[WorkflowStep]] = {}
        self._contexts: Dict[str, WorkflowContext] = {}
        self._running: Set[str] = set()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the workflow engine."""
        self._state = ComponentState.INITIALIZED

    async def cleanup(self) -> None:
        """Clean up workflow engine resources."""
        # Cancel any running workflows
        for workflow_name in list(self._running):
            await self.cancel(workflow_name)

    def _validate_workflow(self, name: str, steps: List[WorkflowStep]) -> None:
        """Validate workflow definition.

        Args:
            name: Workflow name
            steps: Workflow steps

        Raises:
            WorkflowValidationError: If validation fails

        """
        if not steps:
            raise WorkflowValidationError(
                "Workflow must have at least one step",
                workflow=name,
            )

        # Validate step names are unique
        step_names = set()
        for step in steps:
            if step.name in step_names:
                raise WorkflowValidationError(
                    f"Duplicate step name: {step.name}",
                    workflow=name,
                    details={"step": step.name},
                )
            step_names.add(step.name)

    async def register(self, name: str, steps: List[WorkflowStep]) -> None:
        """Register a new workflow.

        Args:
            name: Workflow name
            steps: Workflow steps

        Raises:
            WorkflowValidationError: If registration fails

        """
        try:
            self._validate_workflow(name, steps)
            self._workflows[name] = steps
            self._contexts[name] = WorkflowContext()
            logger.info(
                f"Registered workflow {name}",
                extra={
                    "workflow": name,
                    "steps": len(steps),
                },
            )
        except Exception as e:
            raise WorkflowValidationError(
                f"Failed to register workflow: {e}",
                workflow=name,
            )

    async def execute(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow.

        Args:
            name: Workflow name
            inputs: Initial workflow inputs

        Returns:
            Workflow execution results

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            WorkflowError: If execution fails

        """
        if name not in self._workflows:
            raise WorkflowNotFoundError(name)

        async with self._lock:
            if name in self._running:
                raise WorkflowError(
                    f"Workflow {name} is already running",
                    workflow=name,
                )
            self._running.add(name)

        try:
            context = self._contexts[name]
            context.variables.update(inputs)
            context.state = WorkflowState.RUNNING

            for step in self._workflows[name]:
                # Check step condition
                if step.condition and not self._evaluate_condition(
                    step.condition, context
                ):
                    logger.info(
                        f"Skipping step {step.name} (condition not met)",
                        extra={
                            "workflow": name,
                            "step": step.name,
                        },
                    )
                    continue

                context.set_current_step(step.name)
                try:
                    result = await self._execute_step(step, context, name)
                    if step.outputs:
                        for output in step.outputs:
                            context.variables[output] = result[output]

                    context.add_history_entry(
                        {
                            "step": step.name,
                            "status": "completed",
                            "result": result,
                        }
                    )
                except Exception as e:
                    context.set_error(e)
                    raise StepExecutionError(
                        f"Step {step.name} failed: {e}",
                        workflow=name,
                        step=step.name,
                    )

            context.state = WorkflowState.COMPLETED
            return context.variables

        except Exception:
            context.state = WorkflowState.FAILED
            raise
        finally:
            self._running.remove(name)

    async def cancel(self, name: str) -> None:
        """Cancel a running workflow.

        Args:
            name: Workflow name

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist

        """
        if name not in self._workflows:
            raise WorkflowNotFoundError(name)

        context = self._contexts[name]
        if context.state != WorkflowState.RUNNING:
            return

        context.state = WorkflowState.CANCELLED
        self._running.discard(name)

    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate step condition.

        Args:
            condition: Condition expression
            context: Workflow context

        Returns:
            True if condition is met

        """
        try:
            # Simple condition evaluation for now
            # TODO: Implement proper condition parser
            return eval(condition, {"context": context})
        except Exception as e:
            logger.error(
                f"Failed to evaluate condition: {e}",
                extra={"condition": condition},
            )
            return False

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_name: str,
    ) -> Dict[str, Any]:
        """Execute a workflow step.

        Args:
            step: Step to execute
            context: Workflow context
            workflow_name: Name of the workflow

        Returns:
            Step execution results

        Raises:
            StepExecutionError: If step execution fails
            StepTimeoutError: If step execution times out

        """
        logger.info(
            f"Executing step {step.name}",
            extra={
                "step": step.name,
                "action": step.action,
            },
        )

        # Set up timeout if specified
        if step.timeout:
            try:
                return await asyncio.wait_for(
                    self._execute_action(step, context, workflow_name),
                    timeout=step.timeout,
                )
            except asyncio.TimeoutError:
                raise StepTimeoutError(
                    workflow_name,
                    step.name,
                    step.timeout,
                )
        else:
            return await self._execute_action(step, context, workflow_name)

    async def _execute_action(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_name: str,
    ) -> Dict[str, Any]:
        """Execute step action with retry support.

        Args:
            step: Step to execute
            context: Workflow context
            workflow_name: Name of the workflow

        Returns:
            Action execution results

        Raises:
            StepExecutionError: If action execution fails

        """
        retry_count = 0
        max_retries = (
            step.retry_config.get("max_retries", 0) if step.retry_config else 0
        )
        retry_delay = step.retry_config.get("delay", 1.0) if step.retry_config else 1.0

        while True:
            try:
                # TODO: Implement action registry and execution
                # For now, just return a dummy result
                return {"result": f"Executed {step.action}"}

            except Exception as e:
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        f"Step {step.name} failed, retrying ({retry_count}/{max_retries})",
                        extra={
                            "step": step.name,
                            "error": str(e),
                            "retry": retry_count,
                        },
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                raise StepExecutionError(
                    f"Step {step.name} failed after {retry_count} retries: {e}",
                    workflow=workflow_name,
                    step=step.name,
                    details={
                        "retries": retry_count,
                        "error": str(e),
                    },
                )
