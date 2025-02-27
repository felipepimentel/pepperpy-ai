"""Base classes and interfaces for the unified workflow system.

This module provides the core abstractions for the workflow system:
- WorkflowStep: Represents a single step in a workflow
- WorkflowDefinition: Defines the structure of a workflow
- BaseWorkflow: Base implementation of a workflow
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ..core.base.common import BaseComponent


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    id: str
    name: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_dependency(self, step_id: str) -> None:
        """Add a dependency on another step.

        Args:
            step_id: ID of the step this step depends on
        """
        if step_id not in self.dependencies:
            self.dependencies.append(step_id)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the step.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value


class WorkflowDefinition:
    """Defines the structure of a workflow."""

    def __init__(self, name: str) -> None:
        """Initialize workflow definition.

        Args:
            name: Workflow name
        """
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow.

        Args:
            step: Step to add

        Raises:
            ValueError: If step ID already exists
        """
        if step.id in self.steps:
            raise ValueError(f"Step with ID '{step.id}' already exists")
        self.steps[step.id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID.

        Args:
            step_id: Step ID

        Returns:
            Step if found, None otherwise
        """
        return self.steps.get(step_id)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the workflow.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def validate(self) -> List[str]:
        """Validate the workflow definition.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Check for cycles in dependencies
        visited: Set[str] = set()
        path: List[str] = []

        def check_cycle(step_id: str) -> bool:
            """Check for cycles in dependencies.

            Args:
                step_id: Step ID to check

            Returns:
                True if cycle found, False otherwise
            """
            if step_id in path:
                cycle_path = path[path.index(step_id) :] + [step_id]
                errors.append(f"Dependency cycle detected: {' -> '.join(cycle_path)}")
                return True

            if step_id in visited:
                return False

            visited.add(step_id)
            path.append(step_id)

            step = self.steps.get(step_id)
            if step:
                for dep_id in step.dependencies:
                    if dep_id not in self.steps:
                        errors.append(
                            f"Step '{step_id}' depends on non-existent step '{dep_id}'"
                        )
                    elif check_cycle(dep_id):
                        return True

            path.pop()
            return False

        for step_id in self.steps:
            check_cycle(step_id)

        return errors


class BaseWorkflow(BaseComponent):
    """Base implementation of a workflow."""

    def __init__(self, definition: WorkflowDefinition) -> None:
        """Initialize workflow.

        Args:
            definition: Workflow definition
        """
        super().__init__(definition.name)
        self.definition = definition
        self.state: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the workflow.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.definition.add_metadata(key, value)

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the workflow.

        Args:
            context: Optional execution context

        Returns:
            Workflow results

        Raises:
            ValueError: If workflow definition is invalid
        """
        # Validate workflow
        errors = self.definition.validate()
        if errors:
            raise ValueError(f"Invalid workflow definition: {'; '.join(errors)}")

        # Initialize execution
        self.state = {}
        self.results = {}
        ctx = context or {}

        # Find execution order (topological sort)
        execution_order = self._get_execution_order()

        # Execute steps in order
        for step_id in execution_order:
            step = self.definition.get_step(step_id)
            if step:
                # Prepare step context
                step_context = {**ctx, **self.state}

                # Execute step
                result = await self._execute_step(step, step_context)

                # Store result
                self.results[step_id] = result

                # Update state
                self.state[step_id] = result

        return self.results

    def _get_execution_order(self) -> List[str]:
        """Get the execution order of steps.

        Returns:
            List of step IDs in execution order
        """
        # Topological sort
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        order: List[str] = []

        def visit(step_id: str) -> None:
            """Visit a step in topological sort.

            Args:
                step_id: Step ID to visit
            """
            if step_id in visited:
                return
            if step_id in temp_visited:
                # Cycle detected, but we've already validated
                return

            temp_visited.add(step_id)

            step = self.definition.get_step(step_id)
            if step:
                for dep_id in step.dependencies:
                    visit(dep_id)

            temp_visited.remove(step_id)
            visited.add(step_id)
            order.append(step_id)

        for step_id in self.definition.steps:
            if step_id not in visited:
                visit(step_id)

        # Reverse to get correct order
        return list(reversed(order))

    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute a single step.

        Args:
            step: Step to execute
            context: Execution context

        Returns:
            Step result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        # This is a placeholder implementation
        # Subclasses should override this method
        return {"step_id": step.id, "action": step.action, "status": "executed"}
