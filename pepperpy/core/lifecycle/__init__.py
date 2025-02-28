"""Core lifecycle management module.

This module provides functionality for managing component lifecycles, including:
- Lifecycle states and events
- Lifecycle protocol and base implementation
- Lifecycle hooks and metrics
- Error handling
"""

from pepperpy.common.lifecycle.base import LifecycleComponent
from pepperpy.common.lifecycle.errors import (
    FinalizeError,
    HookError,
    InitializationError,
    RetryError,
    StartError,
    StateError,
    StopError,
    TimeoutError,
)
from pepperpy.common.lifecycle.hooks import LoggingHook, MetricsHook
from pepperpy.common.lifecycle.manager import LifecycleManager
from pepperpy.common.lifecycle.types import (
    Lifecycle,
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleHook,
    LifecycleMetrics,
    LifecycleState,
    LifecycleTransition,
)

__all__ = [
    # Base
    "Lifecycle",
    "LifecycleComponent",
    "LifecycleManager",
    # Types
    "LifecycleState",
    "LifecycleEvent",
    "LifecycleConfig",
    "LifecycleContext",
    "LifecycleHook",
    "LifecycleMetrics",
    "LifecycleTransition",
    # Hooks
    "LoggingHook",
    "MetricsHook",
    # Errors
    "FinalizeError",
    "HookError",
    "InitializationError",
    "RetryError",
    "StartError",
    "StateError",
    "StopError",
    "TimeoutError",
]
