"""Workflow manager module for the Pepperpy framework.

This module provides the workflow manager that handles workflow registration and discovery.
It manages workflow types, configurations, and provides a central point for workflow creation.
"""

import logging
from typing import Dict, List, Optional, Type

from pepperpy.core.errors import WorkflowError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.models import BaseModel
from pepperpy.workflows.definition import WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowManager(Lifecycle):
    """Manages workflow registration, discovery, and creation."""

    def __init__(self) -> None:
        """Initialize workflow manager."""
        super().__init__()
        self._workflows: Dict[str, Type[WorkflowDefinition]] = {}
        self._logger = logger

    def register_workflow(
        self, name: str, workflow_class: Type[WorkflowDefinition]
    ) -> None:
        """Register a workflow type.

        Args:
            name: Workflow type name
            workflow_class: Workflow class to register
        """
        if name in self._workflows:
            raise WorkflowError(f"Workflow type {name} already registered")

        self._workflows[name] = workflow_class
        self._logger.info(f"Registered workflow type: {name}")

    def get_workflow_class(self, name: str) -> Type[WorkflowDefinition]:
        """Get workflow class by name.

        Args:
            name: Workflow type name

        Returns:
            Workflow class

        Raises:
            WorkflowError: If workflow type not found
        """
        if name not in self._workflows:
            raise WorkflowError(f"Workflow type {name} not found")

        return self._workflows[name]

    def list_workflows(self) -> List[str]:
        """List registered workflow types.

        Returns:
            List of workflow type names
        """
        return list(self._workflows.keys())

    async def create_workflow(
        self, name: str, config: Optional[BaseModel] = None
    ) -> WorkflowDefinition:
        """Create a workflow instance.

        Args:
            name: Workflow type name
            config: Optional workflow configuration

        Returns:
            Workflow instance

        Raises:
            WorkflowError: If workflow creation fails
        """
        workflow_class = self.get_workflow_class(name)

        try:
            workflow = workflow_class()
            if config:
                workflow.configure(config)
            await workflow.initialize()
            return workflow
        except Exception as e:
            raise WorkflowError(f"Failed to create workflow {name}: {e}")

    async def _initialize(self) -> None:
        """Initialize workflow manager."""
        self._logger.info("Initializing workflow manager")

    async def _cleanup(self) -> None:
        """Clean up workflow manager resources."""
        self._workflows.clear()
        self._logger.info("Cleaned up workflow manager")
