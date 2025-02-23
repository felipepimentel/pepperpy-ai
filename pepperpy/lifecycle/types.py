"""Lifecycle types module.

This module provides types for the lifecycle system.
"""

from datetime import datetime
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field


class LifecycleState(str, Enum):
    """Lifecycle state enumeration."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    INITIALIZED = "INITIALIZED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FINALIZING = "FINALIZING"
    FINALIZED = "FINALIZED"
    ERROR = "ERROR"


class LifecycleEvent(str, Enum):
    """Lifecycle event enumeration."""

    PRE_INIT = "PRE_INIT"
    POST_INIT = "POST_INIT"
    PRE_START = "PRE_START"
    POST_START = "POST_START"
    PRE_STOP = "PRE_STOP"
    POST_STOP = "POST_STOP"
    PRE_FINALIZE = "PRE_FINALIZE"
    POST_FINALIZE = "POST_FINALIZE"
    ERROR = "ERROR"


class LifecycleConfig(BaseModel):
    """Lifecycle configuration."""

    auto_start: bool = Field(
        default=False, description="Whether to auto-start after initialization"
    )
    auto_finalize: bool = Field(
        default=False, description="Whether to auto-finalize after stop"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")


class LifecycleTransition(BaseModel):
    """Lifecycle transition."""

    from_state: LifecycleState = Field(description="Previous state")
    to_state: LifecycleState = Field(description="New state")
    event: LifecycleEvent = Field(description="Lifecycle event")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Transition timestamp"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Transition metadata"
    )


class LifecycleMetrics(BaseModel):
    """Lifecycle metrics."""

    state: LifecycleState = Field(description="Current state")
    uptime: float = Field(default=0.0, description="Uptime in seconds")
    transitions: int = Field(default=0, description="Number of state transitions")
    errors: int = Field(default=0, description="Number of errors")
    last_transition: datetime | None = Field(
        default=None, description="Last transition timestamp"
    )
    last_error: str | None = Field(default=None, description="Last error message")


class LifecycleContext(BaseModel):
    """Lifecycle context."""

    component_id: str = Field(description="Component ID")
    state: LifecycleState = Field(description="Current state")
    metrics: LifecycleMetrics = Field(description="Lifecycle metrics")
    history: list[LifecycleTransition] = Field(
        default_factory=list, description="State transition history"
    )


class LifecycleHook(Protocol):
    """Lifecycle hook protocol."""

    async def pre_init(self, context: LifecycleContext) -> None:
        """Handle pre-init event.

        Args:
            context: Lifecycle context
        """
        ...

    async def post_init(self, context: LifecycleContext) -> None:
        """Handle post-init event.

        Args:
            context: Lifecycle context
        """
        ...

    async def pre_start(self, context: LifecycleContext) -> None:
        """Handle pre-start event.

        Args:
            context: Lifecycle context
        """
        ...

    async def post_start(self, context: LifecycleContext) -> None:
        """Handle post-start event.

        Args:
            context: Lifecycle context
        """
        ...

    async def pre_stop(self, context: LifecycleContext) -> None:
        """Handle pre-stop event.

        Args:
            context: Lifecycle context
        """
        ...

    async def post_stop(self, context: LifecycleContext) -> None:
        """Handle post-stop event.

        Args:
            context: Lifecycle context
        """
        ...

    async def pre_finalize(self, context: LifecycleContext) -> None:
        """Handle pre-finalize event.

        Args:
            context: Lifecycle context
        """
        ...

    async def post_finalize(self, context: LifecycleContext) -> None:
        """Handle post-finalize event.

        Args:
            context: Lifecycle context
        """
        ...

    async def on_error(self, context: LifecycleContext, error: Exception) -> None:
        """Handle error event.

        Args:
            context: Lifecycle context
            error: Error that occurred
        """
        ...
