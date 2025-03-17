"""
PepperPy Workflows Module.

This module provides workflow functionality for the PepperPy framework.
"""

import asyncio
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from pepperpy.core.errors import PepperPyError

T = TypeVar("T")
R = TypeVar("R")


class WorkflowError(PepperPyError):
    """Base class for workflow errors."""

    pass


class WorkflowStepError(WorkflowError):
    """Error raised when a workflow step fails."""

    def __init__(self, message: str, step_name: str, **kwargs: Any):
        """Initialize a workflow step error.

        Args:
            message: The error message
            step_name: The name of the step that failed
            **kwargs: Additional error metadata
        """
        self.step_name = step_name
        super().__init__(f"{message} (in step: {step_name})", **kwargs)


class WorkflowContext:
    """Context for workflow execution."""

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """Initialize workflow context.

        Args:
            initial_data: Initial data for the context
        """
        self.data = initial_data or {}
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get data from the context.

        Args:
            key: The key to get
            default: The default value to return if the key is not found

        Returns:
            The value for the key, or the default value if the key is not found
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set data in the context.

        Args:
            key: The key to set
            value: The value to set
        """
        self.data[key] = value

    def add_result(self, step_name: str, result: Any) -> None:
        """Add a result for a step.

        Args:
            step_name: The name of the step
            result: The result to add
        """
        self.results[step_name] = result

    def add_error(self, step_name: str, error: Exception) -> None:
        """Add an error for a step.

        Args:
            step_name: The name of the step
            error: The error to add
        """
        self.errors[step_name] = error

    def has_errors(self) -> bool:
        """Check if the context has any errors.

        Returns:
            True if the context has errors, False otherwise
        """
        return bool(self.errors)


class WorkflowStep(Generic[T, R]):
    """A step in a workflow."""

    def __init__(
        self,
        name: str,
        func: Callable[[Any, WorkflowContext], R],
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        required: bool = True,
        condition: Optional[Callable[[WorkflowContext], bool]] = None,
    ):
        """Initialize a workflow step.

        Args:
            name: The name of the step
            func: The function to execute
            input_key: The key to get input data from
            output_key: The key to store output data in
            required: Whether the step is required
            condition: A function that determines whether to execute the step
        """
        self.name = name
        self.func = func
        self.input_key = input_key
        self.output_key = output_key
        self.required = required
        self.condition = condition

    async def execute(self, context: WorkflowContext) -> Optional[R]:
        """Execute the step.

        Args:
            context: The workflow context

        Returns:
            The result of the step, or None if the step was skipped or failed

        Raises:
            WorkflowStepError: If the step fails and is required
        """
        # Check if the step should be executed
        if self.condition is not None and not self.condition(context):
            return None

        try:
            # Get input data
            input_data: Any = None
            if self.input_key is not None:
                input_data = context.get(self.input_key)

            # Execute the step
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(input_data, context)
            else:
                result = self.func(input_data, context)

            # Store the result
            context.add_result(self.name, result)

            # Store the result in the context
            if self.output_key is not None:
                context.set(self.output_key, result)

            return result
        except Exception as e:
            # Add the error to the context
            context.add_error(self.name, e)

            # Raise the error if the step is required
            if self.required:
                raise WorkflowStepError(
                    f"Step {self.name} failed: {str(e)}", self.name
                ) from e

            return None


class Workflow:
    """A workflow of steps."""

    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize a workflow.

        Args:
            name: The name of the workflow
            description: The description of the workflow
        """
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []

    def add_step(self, step: WorkflowStep) -> "Workflow":
        """Add a step to the workflow.

        Args:
            step: The step to add

        Returns:
            The workflow
        """
        self.steps.append(step)
        return self

    async def execute(
        self, context: Optional[WorkflowContext] = None
    ) -> WorkflowContext:
        """Execute the workflow.

        Args:
            context: The workflow context

        Returns:
            The workflow context

        Raises:
            WorkflowError: If the workflow fails
        """
        # Create a context if one wasn't provided
        if context is None:
            context = WorkflowContext()

        # Execute each step
        for step in self.steps:
            try:
                await step.execute(context)

                # Stop if the context has errors
                if context.has_errors() and step.required:
                    break
            except WorkflowStepError:
                # The error is already in the context
                break

        return context


class WorkflowEngine:
    """An engine for executing workflows."""

    def __init__(self):
        """Initialize a workflow engine."""
        self.workflows: Dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow.

        Args:
            workflow: The workflow to register
        """
        self.workflows[workflow.name] = workflow

    async def execute_workflow(
        self, workflow_name: str, context: Optional[WorkflowContext] = None
    ) -> WorkflowContext:
        """Execute a workflow.

        Args:
            workflow_name: The name of the workflow to execute
            context: The workflow context

        Returns:
            The workflow context

        Raises:
            WorkflowError: If the workflow doesn't exist
        """
        # Get the workflow
        workflow = self.workflows.get(workflow_name)
        if workflow is None:
            raise WorkflowError(f"Workflow {workflow_name} not found")

        # Execute the workflow
        return await workflow.execute(context)


__all__ = [
    "Workflow",
    "WorkflowStep",
    "WorkflowEngine",
    "WorkflowContext",
    "WorkflowError",
    "WorkflowStepError",
]
