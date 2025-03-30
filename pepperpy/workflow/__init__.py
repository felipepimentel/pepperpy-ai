"""Workflow module for PepperPy.

This module provides workflow capabilities for PepperPy, allowing
users to create and execute document processing pipelines.
"""

from pepperpy.workflow.base import (
    Workflow,
    WorkflowComponent,
    create_provider,
)

# Importação removida - LocalExecutor agora está em um plugin

__all__ = [
    "Workflow",
    "WorkflowComponent",
    "create_provider",
    # "LocalExecutor",  # Removido - agora está em um plugin
]
