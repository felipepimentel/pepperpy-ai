"""Workflow provider implementations for PepperPy.

This module provides concrete implementations of workflow providers,
supporting different execution environments and patterns.

Example:
    >>> from pepperpy.workflow.providers import LocalExecutor
    >>> workflow = LocalExecutor()
    >>> workflow.add_stage("process", lambda x: x + 1)
    >>> result = await workflow.execute(input=1)
    >>> assert result == 2
"""

from pepperpy.workflow.providers.local import LocalExecutor

__all__ = [
    "LocalExecutor",
]
