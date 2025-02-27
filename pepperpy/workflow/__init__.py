"""Unified workflow system for PepperPy.

This module provides a unified workflow system for PepperPy components:
- Base functionality: Common interfaces and data structures for workflows
- Workflow definition: Structures for defining workflows
- Builder: Fluent API for constructing workflows
- Factory: Creates workflow instances from definitions

This unified system replaces previous fragmented implementations found in:
- workflows/definition/builder.py
- workflows/definition/factory.py

All components should utilize this module for their workflow needs,
with appropriate specialization for specific requirements.
"""

from .base import BaseWorkflow, WorkflowDefinition, WorkflowStep
from .builder import WorkflowBuilder, WorkflowStepBuilder
from .factory import WorkflowFactory, WorkflowRegistry, default_factory

__all__ = [
    # Base
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    # Builder
    "WorkflowBuilder",
    "WorkflowStepBuilder",
    # Factory
    "WorkflowFactory",
    "WorkflowRegistry",
    "default_factory",
]
