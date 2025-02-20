"""Base components for workflow management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowState(Enum):
    """Possible states of a workflow."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow.

    Attributes:
        name: Unique name of the step
        action: Action to execute
        inputs: Input parameters for the action
        outputs: Expected output keys from the action
        condition: Optional condition for step execution
        retry_config: Optional retry configuration
        timeout: Optional timeout in seconds

    """

    name: str
    action: str
    inputs: Dict[str, Any]
    outputs: Optional[List[str]] = None
    condition: Optional[str] = None
    retry_config: Optional[Dict[str, Any]] = None
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowContext:
    """Context for workflow execution.

    Maintains state, variables, and execution history during workflow execution.
    """

    def __init__(self) -> None:
        """Initialize a new workflow context."""
        self.state = WorkflowState.CREATED
        self.variables: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._current_step: Optional[str] = None
        self._error: Optional[Exception] = None

    @property
    def current_step(self) -> Optional[str]:
        """Get the name of the currently executing step."""
        return self._current_step

    @property
    def error(self) -> Optional[Exception]:
        """Get the last error encountered, if any."""
        return self._error

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Get the execution history."""
        return self._history.copy()

    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the execution history.

        Args:
            entry: History entry to add

        """
        self._history.append(entry)

    def set_error(self, error: Exception) -> None:
        """Set the error state.

        Args:
            error: Exception that occurred

        """
        self._error = error
        self.state = WorkflowState.FAILED

    def set_current_step(self, step_name: str) -> None:
        """Set the currently executing step.

        Args:
            step_name: Name of the current step

        """
        self._current_step = step_name
