"""Workflow module for PepperPy framework.

This module provides workflow abstractions for combining multiple components
to achieve specific goals. Workflows are responsible for:
- Component orchestration
- State management
- Error handling
- Progress tracking

Available workflows:
- Base workflow: Base class for all workflows
- Recipes: Ready-to-use workflow recipes for common use cases
"""

from pepperpy.workflow.base import Workflow, WorkflowProvider, create_provider
from pepperpy.workflow.default import DefaultProvider

__all__ = ["Workflow", "WorkflowProvider", "create_provider", "DefaultProvider"]
