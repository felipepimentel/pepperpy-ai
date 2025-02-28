"""Registro central de workflows

Implementa o registro central que gerencia todos os workflows do sistema,
incluindo seu ciclo de vida e estado de execução.
"""

from typing import Dict, List

from pepperpy.core.errors import DuplicateError, NotFoundError
from pepperpy.core.types.enums import WorkflowID

from .base import BaseWorkflow, WorkflowDefinition
from .types import WorkflowStatus


class WorkflowRegistry:
    """Central registry for workflows."""

    def __init__(self) -> None:
        """Initialize workflow registry."""
        self._workflows: Dict[WorkflowID, BaseWorkflow] = {}
        self._definitions: Dict[str, WorkflowDefinition] = {}
        self._status: Dict[WorkflowID, WorkflowStatus] = {}

    def register_workflow(self, workflow: BaseWorkflow) -> None:
        """Register a workflow instance.

        Args:
            workflow: Workflow instance to register

        Raises:
            DuplicateError: If workflow already registered
        """
        workflow_id = workflow.workflow_id
        if workflow_id in self._workflows:
            raise DuplicateError(f"Workflow {workflow_id} already registered")

        self._workflows[workflow_id] = workflow
        self._status[workflow_id] = WorkflowStatus.PENDING

    def register_definition(self, definition: WorkflowDefinition) -> None:
        """Register a workflow definition.

        Args:
            definition: Workflow definition to register

        Raises:
            DuplicateError: If definition already registered
        """
        if definition.name in self._definitions:
            raise DuplicateError(f"Definition {definition.name} already registered")

        self._definitions[definition.name] = definition

    def get_workflow(self, workflow_id: WorkflowID) -> BaseWorkflow:
        """Get a workflow instance by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow instance

        Raises:
            NotFoundError: If workflow not found
        """
        if workflow_id not in self._workflows:
            raise NotFoundError(f"Workflow {workflow_id} not found")

        return self._workflows[workflow_id]

    def get_definition(self, name: str) -> WorkflowDefinition:
        """Get a workflow definition by name.

        Args:
            name: Definition name

        Returns:
            Workflow definition

        Raises:
            NotFoundError: If definition not found
        """
        if name not in self._definitions:
            raise NotFoundError(f"Definition {name} not found")

        return self._definitions[name]

    def get_status(self, workflow_id: WorkflowID) -> WorkflowStatus:
        """Get workflow status.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow status

        Raises:
            NotFoundError: If workflow not found
        """
        if workflow_id not in self._status:
            raise NotFoundError(f"Workflow {workflow_id} not found")

        return self._status[workflow_id]

    def set_status(self, workflow_id: WorkflowID, status: WorkflowStatus) -> None:
        """Set workflow status.

        Args:
            workflow_id: Workflow ID
            status: New status

        Raises:
            NotFoundError: If workflow not found
        """
        if workflow_id not in self._workflows:
            raise NotFoundError(f"Workflow {workflow_id} not found")

        self._status[workflow_id] = status

    def list_workflows(self) -> List[BaseWorkflow]:
        """List all registered workflows.

        Returns:
            List of workflow instances
        """
        return list(self._workflows.values())

    def list_definitions(self) -> List[WorkflowDefinition]:
        """List all registered definitions.

        Returns:
            List of workflow definitions
        """
        return list(self._definitions.values())
