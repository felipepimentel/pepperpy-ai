"""Lifecycle errors for the Pepperpy framework.

This module provides error classes for lifecycle operations.
"""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperError


class LifecycleError(PepperError):
    """Base class for lifecycle errors."""

    def __init__(
        self,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error.

        Args:
            operation: Operation that failed
            details: Optional error details
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            f"Lifecycle operation {operation} failed",
            details=details,
        )
        self.operation = operation
        self.recovery_hint = recovery_hint


class ComponentAlreadyExistsError(LifecycleError):
    """Error raised when a component already exists."""

    def __init__(self, component_name: str) -> None:
        """Initialize the error.

        Args:
            component_name: Name of the existing component
        """
        super().__init__(
            "register",
            details={"component": component_name},
            recovery_hint="Use a different component name or unregister the existing component",
        )


class ComponentNotFoundError(LifecycleError):
    """Error raised when a component is not found."""

    def __init__(self, component_name: str) -> None:
        """Initialize the error.

        Args:
            component_name: Name of the missing component
        """
        super().__init__(
            "lookup",
            details={"component": component_name},
            recovery_hint="Register the component before using it",
        )


__all__ = [
    "LifecycleError",
    "ComponentAlreadyExistsError",
    "ComponentNotFoundError",
]
