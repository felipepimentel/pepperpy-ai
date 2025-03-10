"""
PepperPy Workflows Core Implementation.

This module provides the core implementation of the workflow functionality.
"""

import asyncio
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from pepperpy.errors import PepperPyError

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
        super().__init__(message, step_name=step_name, **kwargs)


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
        """Get a value from the context.

        Args:
            key: The key to get
            default: The default value if the key is not found

        Returns:
            The value for the key, or the default if not found
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context.

        Args:
            key: The key to set
            value: The value to set
        """
        self.data[key] = value

    def add_result(self, step_name: str, result: Any) -> None:
        """Add a step result to the context.

        Args:
            step_name: The name of the step
            result: The result of the step
        """
        self.results[step_name] = result

    def add_error(self, step_name: str, error: Exception) -> None:
        """Add a step error to the context.

        Args:
            step_name: The name of the step
            error: The error that occurred
        """
        self.errors[step_name] = error

    def has_errors(self) -> bool:
        """Check if the context has any errors.

        Returns:
            True if the context has errors, False otherwise
        """
        return len(self.errors) > 0


class WorkflowStep(Generic[T, R]):
    """A step in a workflow."""

    def __init__(
        self,
        name: str,
        func: Callable[[T, WorkflowContext], R],
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        required: bool = True,
        condition: Optional[Callable[[WorkflowContext], bool]] = None,
    ):
        """Initialize a workflow step.

        Args:
            name: The name of the step
            func: The function to execute for this step
            input_key: The key to use for input from the context
            output_key: The key to use for output to the context
            required: Whether this step is required
            condition: A function that determines if this step should run
        """
        self.name = name
        self.func = func
        self.input_key = input_key
        self.output_key = output_key
        self.required = required
        self.condition = condition

    async def execute(self, context: WorkflowContext) -> Optional[R]:
        """Execute this step.

        Args:
            context: The workflow context

        Returns:
            The result of the step, or None if the step was skipped

        Raises:
            WorkflowStepError: If the step fails and is required
        """
        # Check if the step should run
        if self.condition and not self.condition(context):
            return None

        try:
            # Get the input for the step
            input_data = context.get(self.input_key) if self.input_key else None

            # Execute the step with proper type handling
            result = await asyncio.to_thread(self.func, input_data, context)  # type: ignore

            # Store the result
            context.add_result(self.name, result)

            # Store the result in the context if an output key is provided
            if self.output_key:
                context.set(self.output_key, result)

            return result
        except Exception as e:
            # Store the error
            context.add_error(self.name, e)

            # Raise the error if the step is required
            if self.required:
                raise WorkflowStepError(
                    f"Step '{self.name}' failed: {str(e)}", self.name
                ) from e

            return None


class Workflow:
    """A workflow composed of steps."""

    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize a workflow.

        Args:
            name: The name of the workflow
            description: A description of the workflow
        """
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []

    def add_step(self, step: WorkflowStep) -> "Workflow":
        """Add a step to the workflow.

        Args:
            step: The step to add

        Returns:
            The workflow instance for chaining
        """
        self.steps.append(step)
        return self

    async def execute(
        self, context: Optional[WorkflowContext] = None
    ) -> WorkflowContext:
        """Execute the workflow.

        Args:
            context: The workflow context, or None to create a new one

        Returns:
            The workflow context with results

        Raises:
            WorkflowError: If the workflow fails
        """
        # Create a new context if none is provided
        if context is None:
            context = WorkflowContext()

        # Execute each step in sequence
        for step in self.steps:
            try:
                await step.execute(context)
            except WorkflowStepError as e:
                # If a required step fails, the workflow fails
                raise WorkflowError(
                    f"Workflow '{self.name}' failed at step '{e.step_name}': {str(e)}"
                ) from e

        return context


class WorkflowEngine:
    """Engine for executing workflows."""

    def __init__(self):
        """Initialize the workflow engine."""
        self.workflows: Dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow with the engine.

        Args:
            workflow: The workflow to register
        """
        self.workflows[workflow.name] = workflow

    async def execute_workflow(
        self, workflow_name: str, context: Optional[WorkflowContext] = None
    ) -> WorkflowContext:
        """Execute a workflow by name.

        Args:
            workflow_name: The name of the workflow to execute
            context: The workflow context, or None to create a new one

        Returns:
            The workflow context with results

        Raises:
            WorkflowError: If the workflow is not found or fails
        """
        # Get the workflow
        workflow = self.workflows.get(workflow_name)
        if workflow is None:
            raise WorkflowError(f"Workflow '{workflow_name}' not found")

        # Execute the workflow
        return await workflow.execute(context)
