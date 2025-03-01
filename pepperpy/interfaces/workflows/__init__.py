"""Public Interface for workflows

This module provides a stable public interface for the workflows functionality.
It exposes the core workflow abstractions and implementations that are
considered part of the public API.

Core Components:
    BaseWorkflow: Base class for all workflows
    WorkflowDefinition: Definition of workflow structure
    WorkflowStep: Individual step in a workflow
    WorkflowRegistry: Registry for workflow definitions
    WorkflowStatus: Enumeration of workflow execution states

Execution:
    WorkflowExecutor: Executes workflow definitions
    WorkflowScheduler: Schedules workflow execution

Definition:
    WorkflowBuilder: Builds workflow definitions
    WorkflowFactory: Creates workflow instances
"""

# Import public classes and functions from the implementation
from pepperpy.workflows.base import BaseWorkflow, WorkflowDefinition, WorkflowStep
from pepperpy.workflows.builder import WorkflowBuilder
from pepperpy.workflows.execution.executor import WorkflowExecutor
from pepperpy.workflows.execution.scheduler import WorkflowScheduler
from pepperpy.workflows.factory import WorkflowFactory
from pepperpy.workflows.registry import WorkflowRegistry
from pepperpy.workflows.types import WorkflowStatus

__all__ = [
    # Core
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowRegistry",
    "WorkflowStatus",
    # Execution
    "WorkflowExecutor",
    "WorkflowScheduler",
    # Definition
    "WorkflowBuilder",
    "WorkflowFactory",
]
