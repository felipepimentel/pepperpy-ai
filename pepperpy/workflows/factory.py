"""Factory classes for instantiating workflows.

This module provides factory classes for creating workflow instances:
- WorkflowFactory: Creates workflow instances from definitions
"""

import importlib
from typing import Any, Dict, Optional, Type

from .base import BaseWorkflow, WorkflowDefinition, WorkflowStep


class WorkflowRegistry:
    """Registry for workflow implementations."""

    def __init__(self) -> None:
        """Initialize workflow registry."""
        self._workflows: Dict[str, Type[BaseWorkflow]] = {}

    def register(self, action: str, workflow_class: Type[BaseWorkflow]) -> None:
        """Register a workflow implementation.

        Args:
            action: Action identifier
            workflow_class: Workflow class to register

        """
        self._workflows[action] = workflow_class

    def get(self, action: str) -> Optional[Type[BaseWorkflow]]:
        """Get a workflow implementation by action.

        Args:
            action: Action identifier

        Returns:
            Workflow class if registered, None otherwise

        """
        return self._workflows.get(action)


class WorkflowFactory:
    """Factory for creating workflow instances."""

    def __init__(self) -> None:
        """Initialize workflow factory."""
        self.registry = WorkflowRegistry()
        self._default_workflow_class: Type[BaseWorkflow] = BaseWorkflow

    def register_workflow(
        self, action: str, workflow_class: Type[BaseWorkflow],
    ) -> None:
        """Register a workflow implementation.

        Args:
            action: Action identifier
            workflow_class: Workflow class to register

        """
        self.registry.register(action, workflow_class)

    def set_default_workflow_class(self, workflow_class: Type[BaseWorkflow]) -> None:
        """Set the default workflow class.

        Args:
            workflow_class: Default workflow class

        """
        self._default_workflow_class = workflow_class

    def create(self, definition: WorkflowDefinition) -> BaseWorkflow:
        """Create a workflow instance from a definition.

        Args:
            definition: Workflow definition

        Returns:
            Workflow instance

        """
        # Check if there's a specific workflow class for this definition
        workflow_type = definition.metadata.get("workflow_type")
        if workflow_type:
            workflow_class = self.registry.get(workflow_type)
            if workflow_class:
                return workflow_class(definition)

        # Fall back to default workflow class
        return self._default_workflow_class(definition)

    def create_from_dict(self, data: Dict[str, Any]) -> BaseWorkflow:
        """Create a workflow instance from a dictionary.

        Args:
            data: Dictionary representation of a workflow

        Returns:
            Workflow instance

        Raises:
            ValueError: If data is invalid

        """
        if "name" not in data:
            raise ValueError("Workflow definition must have a name")

        definition = WorkflowDefinition(data["name"])

        # Add metadata
        metadata = data.get("metadata", {})
        for key, value in metadata.items():
            definition.add_metadata(key, value)

        # Add steps
        steps = data.get("steps", {})
        for step_id, step_data in steps.items():
            if "name" not in step_data or "action" not in step_data:
                raise ValueError(f"Step '{step_id}' must have name and action")

            # Create step
            step = WorkflowStep(
                id=step_id,
                name=step_data["name"],
                action=step_data["action"],
                parameters=step_data.get("parameters", {}),
            )

            # Add step to definition
            definition.add_step(step)

            # Add dependencies
            dependencies = step_data.get("dependencies", [])
            for dep_id in dependencies:
                step.add_dependency(dep_id)

            # Add metadata
            step_metadata = step_data.get("metadata", {})
            for key, value in step_metadata.items():
                step.add_metadata(key, value)

        return self.create(definition)

    def load_from_module(
        self, module_path: str, attr_name: str = "workflow",
    ) -> BaseWorkflow:
        """Load a workflow from a Python module.

        Args:
            module_path: Dotted path to the module
            attr_name: Attribute name in the module

        Returns:
            Workflow instance

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If attribute does not exist
            TypeError: If attribute is not a WorkflowDefinition or BaseWorkflow

        """
        module = importlib.import_module(module_path)
        attr = getattr(module, attr_name)

        if isinstance(attr, WorkflowDefinition):
            return self.create(attr)
        if isinstance(attr, BaseWorkflow):
            return attr
        raise TypeError(
            f"Expected WorkflowDefinition or BaseWorkflow, got {type(attr).__name__}",
        )


# Global factory instance
default_factory = WorkflowFactory()
