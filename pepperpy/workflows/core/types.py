"""Tipos e enums para o módulo de workflows

Define os tipos de dados e enumerações utilizados no módulo de workflows.
"""

from enum import Enum, auto
from typing import Any, Dict, Protocol, TypeVar

from pepperpy.core.common.types.base import BaseComponent

from .base import BaseWorkflow


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class WorkflowPriority(Enum):
    """Workflow execution priority."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class WorkflowCallback(Protocol):
    """Protocol for workflow callbacks."""

    async def on_start(self, workflow_id: str) -> None:
        """Called when workflow starts.

        Args:
            workflow_id: Workflow ID
        """
        ...

    async def on_pause(self, workflow_id: str) -> None:
        """Called when workflow is paused."""
        ...

    async def on_resume(self, workflow_id: str) -> None:
        """Called when workflow resumes."""
        ...

    async def on_complete(self, workflow_id: str) -> None:
        """Called when workflow completes.

        Args:
            workflow_id: Workflow ID
        """
        ...

    async def on_error(self, workflow_id: str, error: Exception) -> None:
        """Called when workflow encounters an error.

        Args:
            workflow_id: Workflow ID
            error: Error that occurred
        """
        ...

    async def on_step_start(self, workflow_id: str, step_name: str) -> None:
        """Called when workflow step starts.

        Args:
            workflow_id: Workflow ID
            step_name: Step name
        """
        ...

    async def on_step_complete(
        self,
        workflow_id: str,
        step_name: str,
        result: Any,
    ) -> None:
        """Called when workflow step completes.

        Args:
            workflow_id: Workflow ID
            step_name: Step name
            result: Step result
        """
        ...


# Type aliases
WorkflowConfig = Dict[str, Any]
WorkflowResult = Dict[str, Any]

# Type variables
T = TypeVar("T", bound=BaseComponent)
WorkflowT = TypeVar("WorkflowT", bound=BaseWorkflow)
