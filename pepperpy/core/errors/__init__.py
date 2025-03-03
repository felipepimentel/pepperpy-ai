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
    ConfigError,
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
    "ConfigError",
    "PepperError",
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

