"""Workflow executor

Implements the executor that manages the execution of workflows,
including parallelism, error handling, and monitoring.
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.errors import ExecutionError
from pepperpy.core.types.enums import WorkflowID

from ..core.base import BaseWorkflow, WorkflowStep
from ..core.types import WorkflowCallback


class WorkflowExecutor:
    """Executor for workflow instances."""

    def __init__(self, callback: Optional[WorkflowCallback] = None) -> None:
        """Initialize workflow executor.

        Args:
            callback: Optional workflow callback
        """
        self._callback = callback
        self._active_workflows: Dict[WorkflowID, BaseWorkflow] = {}
        self._results: Dict[WorkflowID, Dict[str, Any]] = {}

    async def execute(self, workflow: BaseWorkflow) -> Dict[str, Any]:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute

        Returns:
            Workflow results

        Raises:
            ExecutionError: If execution fails
        """
        workflow_id = workflow.workflow_id
        self._active_workflows[workflow_id] = workflow
        self._results[workflow_id] = {}

        try:
            # Start workflow
            if self._callback:
                await self._callback.on_start(str(workflow_id))

            # Execute steps
            for step in workflow.definition.get_steps():
                result = await self._execute_step(workflow_id, step)
                self._results[workflow_id][step.name] = result

            # Complete workflow
            if self._callback:
                await self._callback.on_complete(str(workflow_id))

            return self._results[workflow_id]

        except Exception as e:
            if self._callback:
                await self._callback.on_error(str(workflow_id), e)
            raise ExecutionError(f"Workflow execution failed: {e}") from e

        finally:
            # Cleanup
            if workflow_id in self._active_workflows:
                del self._active_workflows[workflow_id]

    async def _execute_step(self, workflow_id: WorkflowID, step: WorkflowStep) -> Any:
        """Execute a workflow step.

        Args:
            workflow_id: Workflow ID
            step: Step to execute

        Returns:
            Step result

        Raises:
            ExecutionError: If step execution fails
        """
        try:
            # Start step
            if self._callback:
                await self._callback.on_step_start(str(workflow_id), step.name)

            # Execute step
            result = await step.execute()

            # Complete step
            if self._callback:
                await self._callback.on_step_complete(
                    str(workflow_id), step.name, result
                )

            return result

        except Exception as e:
            raise ExecutionError(f"Step {step.name} execution failed: {e}") from e

    def get_active_workflows(self) -> List[BaseWorkflow]:
        """Get list of active workflows.

        Returns:
            List of active workflow instances
        """
        return list(self._active_workflows.values())

    def get_workflow_result(self, workflow_id: WorkflowID) -> Optional[Dict[str, Any]]:
        """Get workflow results.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow results if available
        """
        return self._results.get(workflow_id)
