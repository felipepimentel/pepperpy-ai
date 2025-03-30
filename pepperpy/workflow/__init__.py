"""Workflow module for PepperPy.

This module provides workflow capabilities for PepperPy, allowing
users to create and execute document processing pipelines.
"""

from pepperpy.workflow.base import (
    Workflow,
    WorkflowComponent,
    create_provider,
)
from pepperpy.workflow.providers.local import LocalExecutor

__all__ = [
    "Workflow",
    "WorkflowComponent",
    "create_provider",
    "LocalExecutor",
]
