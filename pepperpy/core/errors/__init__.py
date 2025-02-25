"""Core error classes."""

from typing import Any, Dict, Optional


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize error.

        Args:
            message: Error message
            **kwargs: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.context = kwargs


class ComponentError(PepperpyError):
    """Error raised when a component operation fails."""

    def __init__(
        self, message: str, component_id: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            component_id: Optional component ID
            **kwargs: Additional error context
        """
        super().__init__(message, component_id=component_id, **kwargs)
        self.component_id = component_id


class StateError(PepperpyError):
    """Error raised when an invalid state transition is attempted."""

    def __init__(
        self,
        message: str,
        component_id: str | None = None,
        current_state: str | None = None,
        target_state: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            component_id: Optional component ID
            current_state: Optional current state
            target_state: Optional target state
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            component_id=component_id,
            current_state=current_state,
            target_state=target_state,
            **kwargs,
        )
        self.component_id = component_id
        self.current_state = current_state
        self.target_state = target_state


class TimeoutError(PepperpyError):
    """Error raised when an operation times out."""

    def __init__(
        self,
        message: str,
        component_id: str | None = None,
        operation: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            component_id: Optional component ID
            operation: Optional operation name
            timeout: Optional timeout value
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            component_id=component_id,
            operation=operation,
            timeout=timeout,
            **kwargs,
        )
        self.component_id = component_id
        self.operation = operation
        self.timeout = timeout


class LifecycleError(ComponentError):
    """Error raised when a lifecycle operation fails."""

    def __init__(
        self,
        message: str,
        component_id: str | None = None,
        state: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            component_id: Optional component ID
            state: Optional component state
            operation: Optional operation name
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            component_id=component_id,
            state=state,
            operation=operation,
            **kwargs,
        )
        self.state = state
        self.operation = operation
 