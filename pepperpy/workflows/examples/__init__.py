"""Example workflows for the PepperPy framework.

This module provides example workflow implementations to demonstrate
the workflow system's capabilities and serve as reference implementations.

Examples:
    - HelloWorld: Simple workflow that demonstrates basic workflow functionality
    - Actions: Example workflow actions that can be used in workflows
"""

from .actions import HelloWorldAction, RandomDelayAction
from .hello_world import HelloWorldWorkflow

__all__ = [
    "HelloWorldWorkflow",
    "HelloWorldAction",
    "RandomDelayAction",
]
