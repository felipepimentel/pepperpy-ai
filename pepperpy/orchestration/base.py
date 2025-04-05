"""
Base Orchestration Provider.

This module defines the base interface for workflow orchestration providers.
"""

from abc import abstractmethod
from typing import Any

from pepperpy.workflow.models import Workflow, WorkflowExecution


class OrchestrationProvider:
    """Base class for workflow orchestration providers.

    An orchestration provider is responsible for executing workflows and managing
    their lifecycle, handling task dependencies, state management, and execution flow.
    It is separate from the workflow implementation itself, which defines the
    business logic to be executed.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize orchestration provider.

        Args:
            **kwargs: Provider configuration
        """
        self.initialized = False
        self.workflows: dict[str, Workflow] = {}
        self.executions: dict[str, WorkflowExecution] = {}

    async def initialize(self) -> None:
        """Initialize the provider."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False

    @abstractmethod
    async def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow with this provider.

        Args:
            workflow: Workflow to register
        """
        pass

    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        """Get a registered workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_workflows(self) -> list[Workflow]:
        """List all registered workflows.

        Returns:
            List of registered workflows
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        """Get a workflow execution by ID.

        Args:
            execution_id: Execution ID

        Returns:
            Execution if found, None otherwise
        """
        pass

    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution.

        Args:
            execution_id: Execution ID

        Returns:
            True if execution was cancelled, False otherwise
        """
        pass

    @abstractmethod
    async def list_executions(
        self, workflow_id: str | None = None
    ) -> list[WorkflowExecution]:
        """List workflow executions.

        Args:
            workflow_id: Optional workflow ID to filter by

        Returns:
            List of workflow executions
        """
        pass
