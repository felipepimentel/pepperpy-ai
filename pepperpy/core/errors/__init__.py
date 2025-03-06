"""Error handling system for PepperPy.

This module defines the framework's error handling system,
providing:

- Exception Hierarchy
  - Validation errors
  - Configuration errors
  - Execution errors
  - System errors

- Error Handling
  - Capturing and propagating
  - Contextualization
  - Structured Logging
  - Recovery

- Categorization
  - By severity
  - By origin
  - By impact
  - By necessary action

The error system is designed to:
- Facilitate diagnosis
- Allow graceful recovery
- Maintain traceability
- Improve developer experience
"""

from typing import Any, Dict, List, Optional, Union

from .base import (
    AgentError,
    ConfigError,
    LifecycleError,
    PepperError,
    StateError,
    ValidationError,
    VersionCompatibilityError,
    VersionDependencyError,
    VersionMigrationError,
    VersionParseError,
    VersionValidationError,
    WorkflowError,
)

__version__ = "0.1.0"
__all__ = [
    "AgentError",
    "ComponentNotFoundError",
    "ConfigError",
    "DuplicateError",
    "ExecutionError",
    "LifecycleError",
    "NotFoundError",
    "PepperError",
    "PepperPyError",
    "StateError",
    "ValidationError",
    "VersionCompatibilityError",
    "VersionDependencyError",
    "VersionMigrationError",
    "VersionParseError",
    "VersionValidationError",
    "WorkflowError",
]


class PepperPyError(Exception):
    """Base class for all PepperPy exceptions."""

    def __init__(self, message: str, *args: Any) -> None:
        """Initialize error.

        Args:
            message: Error message
            *args: Additional arguments

        """
        super().__init__(message, *args)
        self.message = message


class ExecutionError(PepperPyError):
    """Raised when workflow execution fails."""


class DuplicateError(PepperPyError):
    """Raised when attempting to register a duplicate item."""


class NotFoundError(PepperPyError):
    """Raised when an item is not found."""


class ComponentNotFoundError(NotFoundError):
    """Raised when a component is not found.

    This error is raised when attempting to access a component
    that does not exist or has not been registered.
    """

    def __init__(self, component_type: str, component_id: str, *args: Any) -> None:
        """Initialize error.

        Args:
            component_type: Type of component (e.g., "source", "processor")
            component_id: ID of the component that was not found
            *args: Additional arguments
        """
        message = (
            f"Component of type '{component_type}' with ID '{component_id}' not found"
        )
        super().__init__(message, *args)
        self.component_type = component_type
        self.component_id = component_id
