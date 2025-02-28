"""Builder classes for constructing workflows.

This module provides builder classes for constructing workflows:
- WorkflowBuilder: Fluent API for building workflow definitions
"""

from typing import Any, Dict, List, Optional, Union

from .base import WorkflowDefinition, WorkflowStep


class WorkflowBuilder:
    """Builder for constructing workflow definitions using a fluent API."""

    def __init__(self, name: str) -> None:
        """Initialize workflow builder.

        Args:
            name: Name of the workflow
        """
        self.definition = WorkflowDefinition(name)
        self.current_step_id: Optional[str] = None

    def add_step(
        self,
        step_id: str,
        name: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "WorkflowBuilder":
        """Add a step to the workflow.

        Args:
            step_id: Unique identifier for the step
            name: Human-readable name for the step
            action: Action to perform
            parameters: Parameters for the action

        Returns:
            Self for method chaining

        Raises:
            ValueError: If step ID already exists
        """
        step = WorkflowStep(
            id=step_id,
            name=name,
            action=action,
            parameters=parameters or {},
        )
        self.definition.add_step(step)
        self.current_step_id = step_id
        return self

    def depends_on(self, step_id: Union[str, List[str]]) -> "WorkflowBuilder":
        """Add dependencies to the current step.

        Args:
            step_id: ID or list of IDs of steps the current step depends on

        Returns:
            Self for method chaining

        Raises:
            ValueError: If no current step or dependency doesn't exist
        """
        if not self.current_step_id:
            raise ValueError("No current step to add dependencies to")

        current_step = self.definition.get_step(self.current_step_id)
        if not current_step:
            raise ValueError(f"Current step '{self.current_step_id}' not found")

        if isinstance(step_id, list):
            for sid in step_id:
                if not self.definition.get_step(sid):
                    raise ValueError(f"Dependency step '{sid}' not found")
                current_step.add_dependency(sid)
        else:
            if not self.definition.get_step(step_id):
                raise ValueError(f"Dependency step '{step_id}' not found")
            current_step.add_dependency(step_id)

        return self

    def with_metadata(self, key: str, value: Any) -> "WorkflowBuilder":
        """Add metadata to the current step or workflow.

        If there is a current step, adds metadata to that step.
        Otherwise, adds metadata to the workflow.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for method chaining
        """
        if self.current_step_id:
            step = self.definition.get_step(self.current_step_id)
            if step:
                step.add_metadata(key, value)
        else:
            self.definition.add_metadata(key, value)
        return self

    def build(self) -> WorkflowDefinition:
        """Build and validate the workflow definition.

        Returns:
            Completed workflow definition

        Raises:
            ValueError: If workflow validation fails
        """
        errors = self.definition.validate()
        if errors:
            raise ValueError(f"Invalid workflow definition: {'; '.join(errors)}")
        return self.definition


class WorkflowStepBuilder:
    """Builder for constructing individual workflow steps."""

    def __init__(self, workflow_builder: WorkflowBuilder) -> None:
        """Initialize step builder.

        Args:
            workflow_builder: Parent workflow builder
        """
        self.workflow_builder = workflow_builder

    def add_step(
        self,
        step_id: str,
        name: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "WorkflowStepBuilder":
        """Add a step to the workflow.

        Args:
            step_id: Unique identifier for the step
            name: Human-readable name for the step
            action: Action to perform
            parameters: Parameters for the action

        Returns:
            Self for method chaining
        """
        self.workflow_builder.add_step(step_id, name, action, parameters)
        return self

    def depends_on(self, step_id: Union[str, List[str]]) -> "WorkflowStepBuilder":
        """Add dependencies to the current step.

        Args:
            step_id: ID or list of IDs of steps the current step depends on

        Returns:
            Self for method chaining
        """
        self.workflow_builder.depends_on(step_id)
        return self

    def with_metadata(self, key: str, value: Any) -> "WorkflowStepBuilder":
        """Add metadata to the current step.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for method chaining
        """
        self.workflow_builder.with_metadata(key, value)
        return self

    def done(self) -> WorkflowBuilder:
        """Complete the step and return to the workflow builder.

        Returns:
            Parent workflow builder
        """
        return self.workflow_builder
