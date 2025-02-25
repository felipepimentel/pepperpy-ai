"""Lifecycle errors module.

This module defines specific errors that can occur during lifecycle operations.
"""

from pepperpy.core.errors import LifecycleError


class InitializationError(LifecycleError):
    """Raised when initialization fails."""


class StartError(LifecycleError):
    """Raised when start fails."""


class StopError(LifecycleError):
    """Raised when stop fails."""


class FinalizeError(LifecycleError):
    """Raised when finalization fails."""


class StateError(LifecycleError):
    """Raised when an invalid state transition is attempted."""


class HookError(LifecycleError):
    """Raised when a lifecycle hook fails."""


class RetryError(LifecycleError):
    """Raised when retry attempts are exhausted."""


class TimeoutError(LifecycleError):
    """Raised when a lifecycle operation times out."""
