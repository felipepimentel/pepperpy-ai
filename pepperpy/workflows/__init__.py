"""Workflow system for PepperPy framework (DEPRECATED).

This module provides functionality for defining and executing workflows.
This module is deprecated and will be removed in version 1.0.0 (scheduled for Q3 2023).
Please use the 'pepperpy.workflow' module instead.

The functionality previously provided by this module has been moved:
- workflows/definition/base.py → workflow/base.py
- workflows/definition/builder.py → workflow/builder.py
- workflows/definition/factory.py → workflow/factory.py
"""

import warnings
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

# Import from the new workflow module
from ..workflow.base import BaseWorkflow, WorkflowDefinition, WorkflowStep
from ..workflow.builder import WorkflowBuilder
from ..workflow.factory import WorkflowFactory, WorkflowRegistry


# Define types for backward compatibility
class WorkflowStatus(Enum):
    """Status of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowCallback(Protocol):
    """Callback interface for workflow execution events."""

    def on_start(self, workflow_id: str) -> None: ...
    def on_step_start(self, workflow_id: str, step_id: str) -> None: ...
    def on_step_complete(self, workflow_id: str, step_id: str, result: Any) -> None: ...
    def on_step_error(
        self, workflow_id: str, step_id: str, error: Exception
    ) -> None: ...
    def on_complete(self, workflow_id: str, results: Dict[str, Any]) -> None: ...
    def on_error(self, workflow_id: str, error: Exception) -> None: ...


# Simple executor class that delegates to the new workflow module
class WorkflowExecutor:
    """Executor for workflows."""

    def __init__(self, callback: Optional[WorkflowCallback] = None) -> None:
        self.callback = callback

    async def execute(self, workflow: BaseWorkflow, **kwargs: Any) -> Dict[str, Any]:
        """Execute a workflow."""
        return await workflow.execute(**kwargs)


# Show deprecation warning
warnings.warn(
    "The 'pepperpy.workflows' module is deprecated and will be removed in version 1.0.0 (Q3 2023). "
    "Please use 'pepperpy.workflow' module instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowCallback",
    "WorkflowStatus",
    "WorkflowExecutor",
    "WorkflowBuilder",
    "WorkflowFactory",
    "WorkflowRegistry",
]
