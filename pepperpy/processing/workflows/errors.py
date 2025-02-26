"""Workflow-specific error types."""

from typing import Any

from pepperpy.core.errors import PepperError


class WorkflowError(PepperError):
    """Base class for workflow-related errors."""

    def __init__(
        self,
        message: str,
        workflow: str | None = None,
        step: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize workflow error.

        Args:
            message: Error message
            workflow: Name of the workflow
            step: Name of the step
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "WRK000"
        if workflow:
            error_details["workflow"] = workflow
        if step:
            error_details["step"] = step
        super().__init__(message, details=error_details)


class WorkflowNotFoundError(WorkflowError):
    """Error raised when a workflow is not found."""

    def __init__(self, workflow: str) -> None:
        """Initialize workflow not found error.

        Args:
            workflow: Name of the workflow that was not found
        """
        error_details = {"error_code": "WRK001"}
        super().__init__(
            f"Workflow {workflow} not found",
            workflow=workflow,
            details=error_details,
        )


class WorkflowValidationError(WorkflowError):
    """Error raised when workflow validation fails."""

    def __init__(
        self,
        message: str,
        workflow: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize workflow validation error.

        Args:
            message: Error message
            workflow: Name of the workflow
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "WRK002"
        super().__init__(
            message,
            workflow=workflow,
            details=error_details,
        )


class StepExecutionError(WorkflowError):
    """Error raised when step execution fails."""

    def __init__(
        self,
        message: str,
        workflow: str,
        step: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize step execution error.

        Args:
            message: Error message
            workflow: Name of the workflow
            step: Name of the step
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "WRK003"
        super().__init__(
            message,
            workflow=workflow,
            step=step,
            details=error_details,
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
        error_details = {
            "error_code": "WRK004",
            "timeout": timeout,
        }
        super().__init__(
            f"Step {step} timed out after {timeout}s",
            workflow=workflow,
            step=step,
            details=error_details,
        )
