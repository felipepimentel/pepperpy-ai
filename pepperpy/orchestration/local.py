"""
Local Orchestration Provider for PepperPy.

This module provides a local execution provider for workflow orchestration,
running all tasks in-process using asyncio.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from pepperpy.core import get_logger
from pepperpy.orchestration.base import OrchestrationProvider
from pepperpy.workflow.models import (
    ExecutionStatus,
    Task,
    TaskExecution,
    TaskStatus,
    Workflow,
    WorkflowExecution,
)


class LocalOrchestrationProvider(OrchestrationProvider):
    """Local workflow orchestration provider.

    This provider executes workflows locally in the current process,
    managing task dependencies and execution order.
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 5,
        execution_timeout: int = 300,
        **kwargs,
    ):
        """Initialize the local orchestration provider.

        Args:
            max_concurrent_tasks: Maximum number of tasks to execute concurrently
            execution_timeout: Maximum execution time for a workflow in seconds
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.max_concurrent_tasks = max_concurrent_tasks
        self.execution_timeout = execution_timeout
        self.logger = get_logger("orchestration.local")

    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
        self.logger.debug("Initializing local orchestration provider")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.debug("Cleaning up local orchestration provider")
        # Cancel any running executions
        for execution_id, execution in self.executions.items():
            if execution.status == ExecutionStatus.RUNNING:
                await self.cancel_execution(execution_id)
        await super().cleanup()

    async def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow with this provider.

        Args:
            workflow: Workflow to register
        """
        self.workflows[workflow.id] = workflow
        self.logger.debug(f"Registered workflow {workflow.id}: {workflow.name}")

    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        """Get a registered workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        return self.workflows.get(workflow_id)

    async def list_workflows(self) -> list[Workflow]:
        """List all registered workflows.

        Returns:
            List of registered workflows
        """
        return list(self.workflows.values())

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> str:
        """Execute a workflow.

        Args:
            workflow_id: Workflow ID
            inputs: Workflow inputs
            execution_id: Optional execution ID (generated if not provided)

        Returns:
            Execution ID

        Raises:
            ValueError: If workflow not found
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Create execution record
        execution_id = execution_id or str(uuid.uuid4())
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.PENDING,
            inputs=inputs or {},
            created_at=datetime.now(),
        )
        self.executions[execution_id] = execution

        # Start execution in background
        asyncio.create_task(self._execute_workflow_tasks(execution))

        self.logger.info(
            f"Started workflow execution {execution_id} for workflow {workflow_id}"
        )
        return execution_id

    async def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        """Get a workflow execution by ID.

        Args:
            execution_id: Execution ID

        Returns:
            Execution if found, None otherwise
        """
        return self.executions.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution.

        Args:
            execution_id: Execution ID

        Returns:
            True if execution was cancelled, False otherwise
        """
        execution = self.executions.get(execution_id)
        if not execution:
            return False

        # Only cancel if not in terminal state
        if not execution.is_terminal():
            execution.status = ExecutionStatus.CANCELED
            execution.completed_at = datetime.now()
            self.logger.info(f"Cancelled workflow execution {execution_id}")
            return True

        return False

    async def list_executions(
        self, workflow_id: str | None = None
    ) -> list[WorkflowExecution]:
        """List workflow executions.

        Args:
            workflow_id: Optional workflow ID to filter by

        Returns:
            List of workflow executions
        """
        if workflow_id:
            return [
                execution
                for execution in self.executions.values()
                if execution.workflow_id == workflow_id
            ]
        return list(self.executions.values())

    async def _execute_workflow_tasks(self, execution: WorkflowExecution) -> None:
        """Execute the tasks in a workflow.

        This method handles the actual execution of tasks, respecting
        dependencies and managing state.

        Args:
            execution: Workflow execution
        """
        workflow = await self.get_workflow(execution.workflow_id)
        if not workflow:
            execution.status = ExecutionStatus.FAILED
            execution.error = f"Workflow {execution.workflow_id} not found"
            return

        try:
            # Update execution status
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.now()

            # Create task executions for all tasks
            task_executions: dict[str, TaskExecution] = {}
            for task_id, task in workflow.tasks.items():
                task_execution = TaskExecution(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    workflow_execution_id=execution.id,
                    status=TaskStatus.PENDING,
                )
                task_executions[task_id] = task_execution
                execution.task_executions[task_execution.id] = task_execution

            # Initialize task state
            completed_tasks: set[str] = set()
            failed_tasks: set[str] = set()
            pending_tasks: set[str] = set(workflow.tasks.keys())
            running_tasks: set[str] = set()

            # Process tasks until all are completed or we hit an error
            while pending_tasks or running_tasks:
                # Check if any running tasks can be started (have all dependencies met)
                ready_tasks = [
                    task_id
                    for task_id in pending_tasks
                    if all(
                        dep in completed_tasks
                        for dep in workflow.get_task_dependencies(task_id)
                    )
                ]

                # Start ready tasks (up to max concurrent)
                while ready_tasks and len(running_tasks) < self.max_concurrent_tasks:
                    task_id = ready_tasks.pop(0)
                    task = workflow.tasks[task_id]
                    task_execution = task_executions[task_id]

                    # Move task to running state
                    pending_tasks.remove(task_id)
                    running_tasks.add(task_id)
                    task_execution.status = TaskStatus.RUNNING
                    task_execution.started_at = datetime.now()

                    # Prepare task inputs
                    task_inputs = self._prepare_task_inputs(
                        task, workflow, task_executions, execution.inputs
                    )
                    task_execution.inputs = task_inputs

                    # Start task execution
                    asyncio.create_task(
                        self._execute_task(
                            task,
                            task_execution,
                            task_executions,
                            running_tasks,
                            completed_tasks,
                            failed_tasks,
                        )
                    )

                # Wait a bit before checking again
                await asyncio.sleep(0.1)

                # Check if we failed
                if failed_tasks:
                    execution.status = ExecutionStatus.FAILED
                    execution.error = "One or more tasks failed"
                    break

            # Update execution status
            if execution.status != ExecutionStatus.FAILED:
                execution.status = ExecutionStatus.COMPLETED

                # Collect outputs from exit tasks
                execution.outputs = {}
                for task_id in workflow.exit_tasks:
                    task_execution = task_executions[task_id]
                    execution.outputs.update(task_execution.outputs)

            execution.completed_at = datetime.now()
            self.logger.info(
                f"Workflow execution {execution.id} completed with status {execution.status}"
            )

        except Exception as e:
            self.logger.exception(f"Error executing workflow: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()

    async def _execute_task(
        self,
        task: Task,
        task_execution: TaskExecution,
        task_executions: dict[str, TaskExecution],
        running_tasks: set[str],
        completed_tasks: set[str],
        failed_tasks: set[str],
    ) -> None:
        """Execute a single task.

        Args:
            task: Task to execute
            task_execution: Task execution record
            task_executions: Dict of all task executions
            running_tasks: Set of currently running task IDs
            completed_tasks: Set of completed task IDs
            failed_tasks: Set of failed task IDs
        """
        try:
            self.logger.debug(f"Executing task {task.id}: {task.name}")

            # Execute the task
            outputs = await task.execute(task_execution.inputs)

            # Update task execution
            task_execution.status = TaskStatus.COMPLETED
            task_execution.outputs = outputs
            task_execution.completed_at = datetime.now()

            # Update task sets
            running_tasks.remove(task.id)
            completed_tasks.add(task.id)

            self.logger.debug(f"Task {task.id} completed successfully")

        except Exception as e:
            self.logger.error(f"Task {task.id} failed: {e}")

            # Update task execution
            task_execution.status = TaskStatus.FAILED
            task_execution.error = str(e)
            task_execution.completed_at = datetime.now()

            # Update task sets
            running_tasks.remove(task.id)
            failed_tasks.add(task.id)

    def _prepare_task_inputs(
        self,
        task: Task,
        workflow: Workflow,
        task_executions: dict[str, TaskExecution],
        workflow_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Prepare inputs for a task.

        This combines workflow inputs with outputs from dependency tasks.

        Args:
            task: Task to prepare inputs for
            workflow: Workflow definition
            task_executions: Dict of task ID to execution
            workflow_inputs: Workflow inputs

        Returns:
            Combined inputs for the task
        """
        # Start with workflow inputs
        inputs = dict(workflow_inputs)

        # Add outputs from dependencies
        for dep_task_id in workflow.get_task_dependencies(task.id):
            dep_task_execution = task_executions[dep_task_id]
            inputs.update(dep_task_execution.outputs)

        return inputs
