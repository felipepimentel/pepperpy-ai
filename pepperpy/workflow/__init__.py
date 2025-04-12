"""
PepperPy Workflow Module.

This module provides workflow implementations and task definitions.
For workflow orchestration and execution, see the orchestration module.
"""

# Import the A2A workflow
from pepperpy.workflow.a2a_workflow import (
    A2ARegistrationStage,
    A2ASetupStage,
    A2ATaskCreationStage,
    A2AWorkflowProvider,
    create_a2a_workflow,
)
from pepperpy.workflow.base import (
    ComponentType,
    Pipeline,
    PipelineConfig,
    PipelineContext,
    PipelineError,
    PipelineRegistry,
    PipelineStage,
    Workflow,
    WorkflowComponent,
    WorkflowError,
    WorkflowProvider,
    create_provider,
)

__all__ = [
    "ComponentType",
    "Pipeline",
    "PipelineConfig",
    "PipelineContext",
    "PipelineError",
    "PipelineRegistry",
    "PipelineStage",
    "Workflow",
    "WorkflowComponent",
    "WorkflowError",
    "WorkflowProvider",
    "create_provider",
    # A2A workflow
    "A2ASetupStage",
    "A2ARegistrationStage",
    "A2ATaskCreationStage",
    "A2AWorkflowProvider",
    "create_a2a_workflow",
]
