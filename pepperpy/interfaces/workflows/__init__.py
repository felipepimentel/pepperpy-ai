"""Public Interface for workflows

This module provides a stable public interface for the workflows functionality.
It exposes the core workflow abstractions and implementations that are
considered part of the public API.

Core Components:
    BaseWorkflow: Base class for all workflows
    WorkflowDefinition: Definition of workflow structure
    WorkflowStep: Individual step in a workflow
    WorkflowRegistry: Registry for workflow definitions

Execution:
    WorkflowExecutor: Executes workflow definitions
    WorkflowRuntime: Runtime environment for workflows
    WorkflowScheduler: Schedules workflow execution

Definition:
    WorkflowBuilder: Builds workflow definitions
    WorkflowFactory: Creates workflow instances
    WorkflowValidator: Validates workflow definitions
"""

# Import public classes and functions from the implementation
from pepperpy.workflows.base import BaseWorkflow, WorkflowDefinition, WorkflowStep
from pepperpy.workflows.core.definition.builder import WorkflowBuilder
from pepperpy.workflows.core.definition.factory import WorkflowFactory
from pepperpy.workflows.core.definition.validator import WorkflowValidator
from pepperpy.workflows.core.registry import WorkflowRegistry
from pepperpy.workflows.core.types import WorkflowStatus
from pepperpy.workflows.execution.executor import WorkflowExecutor

# Comentando importação que não existe
# from pepperpy.workflows.execution.runtime import WorkflowRuntime
from pepperpy.workflows.execution.scheduler import WorkflowScheduler

__all__ = [
    # Core
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowRegistry",
    "WorkflowStatus",
    # Execution
    "WorkflowExecutor",
    # "WorkflowRuntime",  # Comentando classe que não existe
    "WorkflowScheduler",
    # Definition
    "WorkflowBuilder",
    "WorkflowFactory",
    "WorkflowValidator",
]
