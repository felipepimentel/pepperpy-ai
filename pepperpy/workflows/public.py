"""Public Interface for Workflows

This module provides a stable public interface for the workflow functionality.
It exposes the core workflow abstractions and implementations that are
considered part of the public API.

Core Components:
    BaseWorkflow: Base class for all workflows
    WorkflowDefinition: Definition of a workflow
    WorkflowStep: A step in a workflow
    WorkflowStatus: Status of a workflow execution
    WorkflowExecutor: Executes workflows
    WorkflowScheduler: Schedules workflows for execution
    WorkflowBuilder: Builds workflows
    WorkflowFactory: Creates workflows
    WorkflowRegistry: Registry of available workflows
"""

from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class WorkflowStatus(Enum):
    """Status of a workflow execution."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class WorkflowStep:
    """A step in a workflow.

    This class represents a single step in a workflow, with inputs,
    outputs, and execution logic.
    """

    def __init__(
        self, name: str, function: Callable, dependencies: Optional[List[str]] = None
    ):
        """Initialize a workflow step.

        Args:
            name: Step name
            function: Function to execute
            dependencies: Names of steps this step depends on
        """
        self.name = name
        self.function = function
        self.dependencies = dependencies or []


class WorkflowDefinition:
    """Definition of a workflow.

    This class represents the structure of a workflow, including
    its steps, dependencies, and metadata.
    """

    def __init__(self, name: str, description: str = ""):
        """Initialize a workflow definition.

        Args:
            name: Workflow name
            description: Workflow description
        """
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}

    def add_step(self, step: WorkflowStep) -> "WorkflowDefinition":
        """Add a step to the workflow.

        Args:
            step: Step to add

        Returns:
            Self for chaining
        """
        self.steps[step.name] = step
        return self


class BaseWorkflow:
    """Base class for all workflows.

    This class provides the core functionality for workflows,
    including execution, state management, and event handling.
    """

    def __init__(self, definition: WorkflowDefinition):
        """Initialize a workflow.

        Args:
            definition: Workflow definition
        """
        self.definition = definition
        self.status = WorkflowStatus.PENDING

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow.

        Args:
            inputs: Workflow inputs

        Returns:
            Workflow outputs
        """
        self.status = WorkflowStatus.RUNNING
        try:
            # Implementation would execute steps in dependency order
            result = {}  # Placeholder for actual implementation
            self.status = WorkflowStatus.COMPLETED
            return result
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            raise e


class WorkflowExecutor:
    """Executes workflows.

    This class provides functionality for executing workflows,
    including parallel execution, monitoring, and error handling.
    """

    async def execute(
        self, workflow: BaseWorkflow, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            inputs: Workflow inputs

        Returns:
            Workflow outputs
        """
        return await workflow.execute(inputs)


class WorkflowScheduler:
    """Schedules workflows for execution.

    This class provides functionality for scheduling workflows,
    including recurring execution, delayed execution, and cancellation.
    """

    async def schedule(
        self,
        workflow: BaseWorkflow,
        inputs: Dict[str, Any],
        delay: Optional[int] = None,
    ) -> str:
        """Schedule a workflow for execution.

        Args:
            workflow: Workflow to schedule
            inputs: Workflow inputs
            delay: Delay in seconds

        Returns:
            Scheduled workflow ID
        """
        # Implementation would schedule the workflow
        return "workflow-id"  # Placeholder for actual implementation


class WorkflowBuilder:
    """Builds workflows.

    This class provides a fluent interface for building workflows,
    including adding steps, defining dependencies, and setting metadata.
    """

    def __init__(self, name: str, description: str = ""):
        """Initialize a workflow builder.

        Args:
            name: Workflow name
            description: Workflow description
        """
        self.definition = WorkflowDefinition(name, description)

    def add_step(
        self, name: str, function: Callable, dependencies: Optional[List[str]] = None
    ) -> "WorkflowBuilder":
        """Add a step to the workflow.

        Args:
            name: Step name
            function: Function to execute
            dependencies: Names of steps this step depends on

        Returns:
            Self for chaining
        """
        step = WorkflowStep(name, function, dependencies)
        self.definition.add_step(step)
        return self

    def build(self) -> BaseWorkflow:
        """Build the workflow.

        Returns:
            Built workflow
        """
        return BaseWorkflow(self.definition)


class WorkflowFactory:
    """Creates workflows.

    This class provides factory methods for creating workflows
    from various sources, including definitions, templates, and configurations.
    """

    @staticmethod
    def create_workflow(definition: WorkflowDefinition) -> BaseWorkflow:
        """Create a workflow from a definition.

        Args:
            definition: Workflow definition

        Returns:
            Created workflow
        """
        return BaseWorkflow(definition)


class WorkflowRegistry:
    """Registry of available workflows.

    This class provides functionality for registering, retrieving,
    and managing workflows.
    """

    def __init__(self):
        """Initialize a workflow registry."""
        self.workflows: Dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        """Register a workflow definition.

        Args:
            definition: Workflow definition to register
        """
        self.workflows[definition.name] = definition

    def get(self, name: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by name.

        Args:
            name: Workflow name

        Returns:
            Workflow definition or None if not found
        """
        return self.workflows.get(name)


# Export public classes
__all__ = [
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowStatus",
    "WorkflowExecutor",
    "WorkflowScheduler",
    "WorkflowBuilder",
    "WorkflowFactory",
    "WorkflowRegistry",
]
