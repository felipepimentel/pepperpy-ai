"""Workflows Module

This module provides a comprehensive workflow system for building, managing, and executing
AI-powered workflows in the PepperPy framework. It enables the creation of complex, multi-step
processes with proper dependency management, error handling, and monitoring.

Key Components:
- Core: Fundamental workflow abstractions and base components
- Definition: Tools for defining and constructing workflows
- Execution: Runtime environment for workflow execution and monitoring
- Examples: Reference implementations and templates

The workflows system supports:
- Sequential and parallel execution
- Conditional branching and looping
- Error handling and recovery
- State management and persistence
- Monitoring and observability
"""

from .base import BaseWorkflow, WorkflowDefinition, WorkflowStep
from .builder import WorkflowBuilder
from .factory import WorkflowFactory
from .registry import WorkflowRegistry
from .types import WorkflowStatus

# Merged from /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/workflow/__init__.py during consolidation
