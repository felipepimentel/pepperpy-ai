"""Central registry for workflows

Implementa o registro central que gerencia todos os workflows do sistema,
incluindo seu ciclo de vida e estado de execução.
"""

from typing import Dict, List

from pepperpy.core.common.logging import get_logger
from pepperpy.core.common.registry.base import (
    ComponentMetadata,
    Registry,
    get_registry,
)
from pepperpy.core.common.types.enums import WorkflowID
from pepperpy.core.errors import DuplicateError, NotFoundError

from .base import BaseWorkflow, WorkflowDefinition
from .types import WorkflowStatus

logger = get_logger(__name__)


class WorkflowRegistry(Registry[BaseWorkflow]):
    """Central registry for workflows."""

    def __init__(self) -> None:
        """Initialize workflow registry."""
        super().__init__(BaseWorkflow)
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

        metadata = ComponentMetadata(
            id=workflow_id,
            name=workflow.name,
            description=getattr(workflow, "description", ""),
            properties={"status": WorkflowStatus.PENDING.value},
        )

        try:
            self.register(workflow, metadata)
            self._status[workflow_id] = WorkflowStatus.PENDING
        except Exception as e:
            raise DuplicateError(f"Failed to register workflow: {e}") from e

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
        try:
            return self.get(str(workflow_id))
        except Exception as e:
            raise NotFoundError(f"Workflow {workflow_id} not found") from e

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
        if workflow_id not in self._status:
            raise NotFoundError(f"Workflow {workflow_id} not found")

        self._status[workflow_id] = status

        # Update metadata
        try:
            metadata = self.get_metadata(str(workflow_id))
            metadata.properties["status"] = status.value
        except Exception as e:
            logger.warning(f"Failed to update workflow metadata: {e}")

    def list_workflows(self) -> List[BaseWorkflow]:
        """List all registered workflows.

        Returns:
            List of workflow instances
        """
        return list(self.list_components().values())

    def list_definitions(self) -> List[WorkflowDefinition]:
        """List all registered definitions.

        Returns:
            List of workflow definitions
        """
        return list(self._definitions.values())


# Global registry instance
_registry = None


def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry instance."""
    global _registry
    if _registry is None:
        _registry = WorkflowRegistry()
        # Register with the global registry manager
        try:
            registry_manager = get_registry()
            registry_manager.register_registry("workflows", _registry)
        except Exception as e:
            logger.warning(f"Failed to register with global registry: {e}")
    return _registry
