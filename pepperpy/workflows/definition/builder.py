"""Builder for workflow construction.

Implements the Builder pattern for fluent workflow construction.
"""

from typing import Any, Dict, Optional

from ..core.base import BaseWorkflow, WorkflowDefinition, WorkflowStep


class WorkflowBuilder:
    """Builder for constructing workflows."""

    def __init__(self, name: str) -> None:
        """Initialize workflow builder.

        Args:
            name: Workflow name

        """
        self._definition = WorkflowDefinition(name)
        self._current_step: Optional[WorkflowStep] = None
        self._config: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep) -> "WorkflowBuilder":
        """Add a step to the workflow.

        Args:
            step: Step to add

        Returns:
            Builder instance for chaining

        """
        self._definition.add_step(step)
        self._current_step = step
        return self

    def configure(self, **config: Any) -> "WorkflowBuilder":
        """Configure workflow.

        Args:
            **config: Configuration parameters

        Returns:
            Builder instance for chaining

        """
        self._config.update(config)
        return self

    def build(self) -> BaseWorkflow:
        """Build workflow instance.

        Returns:
            Configured workflow instance

        """
        workflow = BaseWorkflow(self._definition)
        for key, value in self._config.items():
            workflow.add_metadata(key, value)
        return workflow
