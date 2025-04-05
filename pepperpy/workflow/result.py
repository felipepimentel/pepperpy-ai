"""
PepperPy Workflow Results.

Result classes specific to workflow operations.
"""

from typing import Any, Optional

from pepperpy.common.result import Result


class WorkflowStepResult(Result):
    """Result of a workflow step execution."""

    def __init__(
        self,
        content: Any,
        step_name: str,
        step_type: str,
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize a workflow step result.

        Args:
            content: Step result content
            step_name: Name of the step
            step_type: Type of step
            metadata: Optional metadata
            logger: Optional logger
        """
        metadata = metadata or {}
        metadata["step_name"] = step_name
        metadata["step_type"] = step_type

        super().__init__(content, metadata, logger)
        self.step_name = step_name
        self.step_type = step_type


class WorkflowResult(Result):
    """Result of a complete workflow execution."""

    def __init__(
        self,
        content: Any,
        step_results: list[WorkflowStepResult],
        workflow_name: str,
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize a workflow result.

        Args:
            content: Final workflow result
            step_results: Results of individual steps
            workflow_name: Name of the workflow
            metadata: Optional metadata
            logger: Optional logger
        """
        metadata = metadata or {}
        metadata["workflow_name"] = workflow_name
        metadata["step_count"] = len(step_results)

        super().__init__(content, metadata, logger)
        self.workflow_name = workflow_name
        self.step_results = step_results

    def get_step_result(self, step_name: str) -> WorkflowStepResult | None:
        """Get a step result by name.

        Args:
            step_name: Name of the step

        Returns:
            Step result or None if not found
        """
        for step in self.step_results:
            if step.step_name == step_name:
                return step
        return None
