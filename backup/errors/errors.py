"""Core error types for Pepperpy."""

from typing import Any, Optional


class PepperpyError(Exception):
    """Base exception class for Pepperpy errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: The error message
        """
        super().__init__(message)
        self.message = message


class ValidationError(PepperpyError):
    """Validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize the error.

        Args:
            message: The error message
            details: Optional error details
        """
        super().__init__(message)
        self.details = details or {}


class ConfigError(PepperpyError):
    """Configuration error."""

    def __init__(self, message: str, config_path: str | None = None):
        """Initialize the error.

        Args:
            message: The error message
            config_path: Optional configuration path
        """
        super().__init__(message)
        self.config_path = config_path


class WorkflowError(PepperpyError):
    """Workflow-related error."""

    def __init__(self, message: str, workflow_id: Optional[str] = None):
        """Initialize the error.

        Args:
            message: The error message
            workflow_id: Optional workflow ID
        """
        if workflow_id:
            super().__init__(f"Workflow error ({workflow_id}): {message}")
            self.workflow_id = workflow_id
        else:
            super().__init__(f"Workflow error: {message}")
            self.workflow_id = None


class ComponentError(PepperpyError):
    """Component-related error."""

    def __init__(self, message: str, component_id: str | None = None):
        """Initialize the error.

        Args:
            message: The error message
            component_id: Optional component ID
        """
        if component_id:
            super().__init__(f"Component error ({component_id}): {message}")
            self.component_id = component_id
        else:
            super().__init__(f"Component error: {message}")
            self.component_id = None


class StateError(PepperpyError):
    """State-related error."""

    def __init__(self, message: str, state: str | None = None):
        """Initialize the error.

        Args:
            message: The error message
            state: Optional state information
        """
        if state:
            super().__init__(f"State error ({state}): {message}")
            self.state = state
        else:
            super().__init__(f"State error: {message}")
            self.state = None


__all__ = [
    "PepperpyError",
    "ValidationError",
    "ConfigError",
    "WorkflowError",
    "ComponentError",
    "StateError",
] 