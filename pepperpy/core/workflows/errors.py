"""Workflow-specific error types."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class WorkflowError(PepperpyError):
    """Base class for workflow-related errors."""

    def __init__(
        self,
        message: str,
        workflow: Optional[str] = None,
        step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize workflow error.

        Args:
            message: Error message
            workflow: Name of the workflow
            step: Name of the step
            details: Additional error details

        """
        super().__init__(
            message,
            error_code="WORKFLOW_ERROR",
            details={
                "workflow": workflow,
                "step": step,
                **(details or {}),
            },
        )


class WorkflowNotFoundError(WorkflowError):
    """Error raised when a workflow is not found."""

    def __init__(self, workflow: str) -> None:
        """Initialize workflow not found error.

        Args:
            workflow: Name of the workflow that was not found

        """
        super().__init__(
            f"Workflow {workflow} not found",
            workflow=workflow,
            details={"error_code": "WORKFLOW_NOT_FOUND"},
        )


class WorkflowValidationError(WorkflowError):
    """Error raised when workflow validation fails."""

    def __init__(
        self,
        message: str,
        workflow: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize workflow validation error.

        Args:
            message: Error message
            workflow: Name of the workflow
            details: Additional error details

        """
        super().__init__(
            message,
            workflow=workflow,
            details={
                "error_code": "WORKFLOW_VALIDATION_ERROR",
                **(details or {}),
            },
        )


class StepExecutionError(WorkflowError):
    """Error raised when step execution fails."""

    def __init__(
        self,
        message: str,
        workflow: str,
        step: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize step execution error.

        Args:
            message: Error message
            workflow: Name of the workflow
            step: Name of the step
            details: Additional error details

        """
        super().__init__(
            message,
            workflow=workflow,
            step=step,
            details={
                "error_code": "STEP_EXECUTION_ERROR",
                **(details or {}),
            },
        )


class StepTimeoutError(StepExecutionError):
    """Error raised when step execution times out."""

    def __init__(
        self,
        workflow: str,
        step: str,
        timeout: float,
    ) -> None:
        """Initialize step timeout error.

        Args:
            workflow: Name of the workflow
            step: Name of the step
            timeout: Timeout value in seconds

        """
        super().__init__(
            f"Step {step} timed out after {timeout}s",
            workflow=workflow,
            step=step,
            details={"timeout": timeout},
        )
