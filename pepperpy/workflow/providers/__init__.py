"""Workflow provider implementations for PepperPy.

This module provides concrete implementations of workflow providers,
supporting different execution environments and patterns.

Example:
    >>> from pepperpy.workflow.providers import LocalWorkflow
    >>> workflow = LocalWorkflow()
    >>> workflow.add_stage("process", lambda x: x + 1)
    >>> result = await workflow.execute(input=1)
    >>> assert result == 2
"""

from pepperpy.workflow.providers.local import LocalWorkflow

__all__ = [
    "LocalWorkflow",
]
