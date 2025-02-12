"""Session management for monitoring teams and workflows."""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from pepperpy.hub.teams import Team, WorkflowProtocol


class BaseSession:
    """Base class for monitoring sessions."""

    def __init__(self):
        """Initialize the session."""
        self._current_step: Optional[str] = None
        self._thoughts: list[str] = []
        self._progress: float = 0.0
        self._needs_input: bool = False
        self._input_prompt: Optional[str] = None

    @property
    def current_step(self) -> Optional[str]:
        """Get the current step being executed."""
        return self._current_step

    @property
    def thoughts(self) -> list[str]:
        """Get the thought process log."""
        return self._thoughts.copy()

    @property
    def progress(self) -> float:
        """Get the progress percentage (0-1)."""
        return self._progress

    @property
    def needs_input(self) -> bool:
        """Check if user input is needed."""
        return self._needs_input

    @property
    def input_prompt(self) -> Optional[str]:
        """Get the prompt for user input if needed."""
        return self._input_prompt

    def provide_input(self, input_value: str) -> None:
        """Provide user input when requested.

        Args:
            input_value: The input value to provide

        """
        if not self._needs_input:
            raise RuntimeError("No input currently requested")
        self._handle_input(input_value)

    def _handle_input(self, input_value: str) -> None:
        """Handle user input."""
        raise NotImplementedError


class TeamSession(BaseSession):
    """Session for monitoring team execution."""

    def __init__(self, team: "Team"):
        """Initialize the team session.

        Args:
            team: The team being monitored

        """
        super().__init__()
        self._team = team
        self._agent_states: dict[str, Any] = {}

    @property
    def agent_states(self) -> dict[str, Any]:
        """Get the current state of each agent."""
        return self._agent_states.copy()

    def _handle_input(self, input_value: str) -> None:
        """Handle user input for the team."""
        # TODO: Implement team input handling
        pass


class WorkflowSession(BaseSession):
    """Session for monitoring workflow execution."""

    def __init__(self, workflow: "WorkflowProtocol"):
        """Initialize the workflow session.

        Args:
            workflow: The workflow being monitored

        """
        super().__init__()
        self._workflow = workflow
        self._step_results: dict[str, Any] = {}
        self._current_step_index: int = 0
        self._total_steps: int = len(getattr(workflow, "_config", {}).get("steps", []))

    @property
    def step_results(self) -> dict[str, Any]:
        """Get the results from completed steps."""
        return self._step_results.copy()

    @property
    def current_step(self) -> Optional[str]:
        """Get the current step being executed."""
        if not self._total_steps:
            return None
        if self._current_step_index >= self._total_steps:
            return None
        steps = getattr(self._workflow, "_config", {}).get("steps", [])
        if not steps:
            return None
        return steps[self._current_step_index].action

    @property
    def progress(self) -> float:
        """Get the progress percentage (0-1)."""
        if not self._total_steps:
            return 1.0
        return min(1.0, self._current_step_index / self._total_steps)

    def _handle_input(self, input_value: str) -> None:
        """Handle user input for the workflow."""
        if not self._needs_input:
            return

        # Store input in step results
        self._step_results[f"step_{self._current_step_index}_input"] = input_value
        self._needs_input = False
        self._input_prompt = None

    def record_step_result(self, result: Any) -> None:
        """Record the result of the current step.

        Args:
            result: The step execution result

        """
        self._step_results[f"step_{self._current_step_index}"] = result
        self._current_step_index += 1


__all__ = ["TeamSession", "WorkflowSession"]
