"""Workflow execution engine."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

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


class RunStatus:
    """Status of a workflow run."""

    def __init__(self, run_id: str) -> None:
        """Initialize run status.

        Args:
            run_id: Run identifier
        """
        self.run_id = run_id
        self.state = WorkflowState.CREATED
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.steps: Dict[str, "StepStatus"] = {}


class StepStatus:
    """Status of a workflow step."""

    def __init__(self, step_id: str) -> None:
        """Initialize step status.

        Args:
            step_id: Step identifier
        """
        self.step_id = step_id
        self.state = WorkflowState.CREATED
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None


class LogEntry:
    """Log entry for a workflow run."""

    def __init__(
        self,
        message: str,
        level: str = "INFO",
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Initialize log entry.

        Args:
            message: Log message
            level: Log level
            timestamp: Optional timestamp
        """
        self.message = message
        self.level = level
        self.timestamp = timestamp or datetime.utcnow()


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
        self._run_status: Dict[str, RunStatus] = {}
        self._run_logs: Dict[str, List[LogEntry]] = {}

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

    async def deploy_workflow(self, definition: Dict[str, Any]) -> str:
        """Deploy a new workflow.

        Args:
            definition: Workflow definition

        Returns:
            str: Workflow ID

        Raises:
            WorkflowValidationError: If deployment fails
        """
        try:
            # Generate workflow ID
            workflow_id = str(uuid.uuid4())

            # Parse steps
            steps = []
            for step_def in definition.get("steps", []):
                step = WorkflowStep(
                    name=step_def["name"],
                    action=step_def["action"],
                    inputs=step_def.get("inputs", {}),
                    outputs=step_def.get("outputs"),
                    condition=step_def.get("condition"),
                    retry_config=step_def.get("retry"),
                    timeout=step_def.get("timeout"),
                    metadata=step_def.get("metadata", {}),
                )
                steps.append(step)

            # Register workflow
            await self.register(workflow_id, steps)

            return workflow_id

        except Exception as e:
            raise WorkflowValidationError(
                f"Failed to deploy workflow: {e}", workflow=workflow_id
            )

    async def start_workflow(self, workflow_id: str, inputs: Dict[str, Any]) -> str:
        """Start a workflow asynchronously.

        Args:
            workflow_id: Workflow ID
            inputs: Workflow inputs

        Returns:
            str: Run ID

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            WorkflowError: If start fails
        """
        if workflow_id not in self._workflows:
            raise WorkflowNotFoundError(workflow_id)

        # Generate run ID
        run_id = str(uuid.uuid4())

        # Initialize run status
        status = RunStatus(run_id)
        self._run_status[run_id] = status

        # Initialize logs
        self._run_logs[run_id] = []

        # Start workflow in background
        asyncio.create_task(self._run_workflow(workflow_id, run_id, inputs))

        return run_id

    async def run_workflow(
        self, workflow_id: str, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a workflow synchronously.

        Args:
            workflow_id: Workflow ID
            inputs: Workflow inputs

        Returns:
            Dict[str, Any]: Workflow results

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            WorkflowError: If execution fails
        """
        run_id = await self.start_workflow(workflow_id, inputs)
        status = await self.get_run_status(run_id)

        while status.state in [WorkflowState.CREATED, WorkflowState.RUNNING]:
            await asyncio.sleep(0.1)
            status = await self.get_run_status(run_id)

        if status.state == WorkflowState.FAILED:
            raise WorkflowError(
                f"Workflow failed: {status.error}", workflow=workflow_id
            )

        return self._contexts[workflow_id].variables

    async def _run_workflow(
        self,
        workflow_id: str,
        run_id: str,
        inputs: Dict[str, Any],
    ) -> None:
        """Run a workflow in the background.

        Args:
            workflow_id: Workflow ID
            run_id: Run ID
            inputs: Workflow inputs
        """
        status = self._run_status[run_id]
        try:
            # Update status
            status.state = WorkflowState.RUNNING
            status.started_at = datetime.utcnow()

            # Execute workflow
            await self.execute(workflow_id, inputs)

            # Update status
            status.state = WorkflowState.COMPLETED
            status.completed_at = datetime.utcnow()

        except Exception as e:
            # Update status
            status.state = WorkflowState.FAILED
            status.error = str(e)
            status.completed_at = datetime.utcnow()

    async def get_run_status(self, run_id: str) -> RunStatus:
        """Get status of a workflow run.

        Args:
            run_id: Run ID

        Returns:
            RunStatus: Run status

        Raises:
            WorkflowError: If run not found
        """
        status = self._run_status.get(run_id)
        if not status:
            raise WorkflowError(f"Run not found: {run_id}", workflow="unknown")
        return status

    async def get_run_logs(self, run_id: str) -> List[LogEntry]:
        """Get logs for a workflow run.

        Args:
            run_id: Run ID

        Returns:
            List[LogEntry]: Run logs

        Raises:
            WorkflowError: If run not found
        """
        logs = self._run_logs.get(run_id)
        if logs is None:
            raise WorkflowError(f"Run not found: {run_id}", workflow="unknown")
        return logs

    async def stop_workflow(self, run_id: str) -> None:
        """Stop a running workflow.

        Args:
            run_id: Run ID

        Raises:
            WorkflowError: If stop fails
        """
        status = self._run_status.get(run_id)
        if not status:
            raise WorkflowError(f"Run not found: {run_id}", workflow="unknown")

        if status.state != WorkflowState.RUNNING:
            return

        status.state = WorkflowState.CANCELLED
        status.completed_at = datetime.utcnow()

    async def delete_workflow(self, workflow_id: str) -> None:
        """Delete a workflow.

        Args:
            workflow_id: Workflow ID

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
        """
        if workflow_id not in self._workflows:
            raise WorkflowNotFoundError(workflow_id)

        # Cancel if running
        if workflow_id in self._running:
            await self.cancel(workflow_id)

        # Remove workflow
        del self._workflows[workflow_id]
        del self._contexts[workflow_id]

    async def list_workflows(
        self,
        state: Optional[WorkflowState] = None,
    ) -> List[Dict[str, Any]]:
        """List workflows.

        Args:
            state: Optional state filter

        Returns:
            List[Dict[str, Any]]: List of workflows
        """
        workflows = []
        for workflow_id, steps in self._workflows.items():
            context = self._contexts[workflow_id]
            if state and context.state != state:
                continue

            workflow = {
                "id": workflow_id,
                "name": steps[0].name if steps else "unnamed",
                "state": context.state,
                "created_at": context.history[0]["timestamp"]
                if context.history
                else None,
                "last_run_at": context.history[-1]["timestamp"]
                if context.history
                else None,
            }
            workflows.append(workflow)

        return workflows

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

                    context.add_history_entry({
                        "step": step.name,
                        "status": "completed",
                        "result": result,
                    })
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
