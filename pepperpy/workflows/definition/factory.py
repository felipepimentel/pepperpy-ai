"""Factory para criação de workflows.

Implementa o padrão Factory para criação de workflows a partir de definições.
"""

from typing import Dict, Optional, Type

from ..core.base import BaseWorkflow, WorkflowDefinition
from ..core.types import WorkflowConfig


class WorkflowFactory:
    """Factory for creating workflow instances."""

    def __init__(self) -> None:
        """Initialize workflow factory."""
        self._workflow_types: Dict[str, Type[BaseWorkflow]] = {}

    def register_type(self, name: str, workflow_type: Type[BaseWorkflow]) -> None:
        """Register a workflow type.

        Args:
            name: Type name
            workflow_type: Workflow class
        """
        self._workflow_types[name] = workflow_type

    def create(
        self,
        workflow_type: str,
        definition: WorkflowDefinition,
        config: Optional[WorkflowConfig] = None,
    ) -> BaseWorkflow:
        """Create a workflow instance.

        Args:
            workflow_type: Type of workflow to create
            definition: Workflow definition
            config: Optional workflow configuration

        Returns:
            Workflow instance

        Raises:
            ValueError: If workflow type not registered
        """
        if workflow_type not in self._workflow_types:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        workflow_class = self._workflow_types[workflow_type]
        workflow = workflow_class(definition)

        if config:
            for key, value in config.items():
                workflow.add_metadata(key, value)

        return workflow
