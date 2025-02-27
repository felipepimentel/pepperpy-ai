"""Core workflow types and data structures.

This module provides the foundational types and data structures used by the workflow system.
It defines the core models for workflow steps, states, and contexts that are used across
both the core engine and higher-level workflow management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pepperpy.core.errors import PepperpyError


class WorkflowState(Enum):
    """States that a workflow can be in."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepState(Enum):
    """States that a workflow step can be in."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Definition of a workflow step.

    A step represents a single unit of work in a workflow, with its own
    inputs, outputs, and execution logic.

    Attributes:
        name: Unique name of the step within the workflow
        action: Name of the action to execute
        inputs: Dictionary of input parameters for the action
        outputs: List of output names to capture from the action
        required: Whether the step must complete successfully
        retry_count: Number of times to retry on failure
        timeout: Optional timeout in seconds
        dependencies: Set of step names this step depends on

    """

    name: str
    action: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: list[str] = field(default_factory=list)
    required: bool = True
    retry_count: int = 0
    timeout: float | None = None
    dependencies: set[str] = field(default_factory=set)


@dataclass
class WorkflowContext:
    """Runtime context for workflow execution.

    This class maintains the state and variables during workflow execution,
    including step results and error information.

    Attributes:
        workflow_id: Unique identifier for the workflow instance
        variables: Dictionary of workflow variables and step outputs
        state: Current state of the workflow
        step_states: Dictionary mapping step names to their states
        errors: List of errors encountered during execution
        history: List of execution history events

    """

    workflow_id: str
    variables: dict[str, Any] = field(default_factory=dict)
    state: WorkflowState = WorkflowState.CREATED
    step_states: dict[str, StepState] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


class WorkflowError(PepperpyError):
    """Base error class for workflow-related errors.

    Attributes:
        workflow_id: ID of the workflow that encountered the error
        step_name: Optional name of the specific step that failed
        details: Optional additional error details

    """

    def __init__(
        self,
        message: str,
        workflow_id: str,
        step_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            workflow_id: ID of the workflow that encountered the error
            step_name: Optional name of the specific step that failed
            details: Optional additional error details

        """
        super().__init__(message)
        self.workflow_id = workflow_id
        self.step_name = step_name
        self.details = details or {}
