"""Core workflows module.

This module provides the workflow engine and related components.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from pepperpy.common.base import Lifecycle
from pepperpy.core.types import ComponentState


class WorkflowStep(BaseModel):
    """Workflow step configuration."""

    name: str = Field(description="Step name")
    type: str = Field(description="Step type")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Step configuration"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Step dependencies"
    )
    enabled: bool = Field(default=True, description="Whether the step is enabled")


class WorkflowConfig(BaseModel):
    """Workflow configuration."""

    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    version: str = Field(description="Workflow version")
    steps: List[WorkflowStep] = Field(
        default_factory=list, description="Workflow steps"
    )
    enabled: bool = Field(default=True, description="Whether the workflow is enabled")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow settings"
    )


class WorkflowEngine(Lifecycle):
    """Engine for executing workflows."""

    def __init__(self) -> None:
        """Initialize workflow engine."""
        self.state = ComponentState.INITIALIZED
        self._workflows: Dict[str, WorkflowConfig] = {}

    async def initialize(self) -> None:
        """Initialize workflow engine."""
        try:
            # TODO: Initialize workflow engine
            self.state = ComponentState.RUNNING

        except Exception:
            self.state = ComponentState.ERROR
            raise

    async def cleanup(self) -> None:
        """Clean up workflow engine."""
        try:
            # TODO: Clean up workflow engine
            self.state = ComponentState.STOPPED

        except Exception:
            self.state = ComponentState.ERROR
            raise

    async def register_workflow(self, workflow: WorkflowConfig) -> None:
        """Register a workflow.

        Args:
            workflow: Workflow configuration
        """
        self._workflows[workflow.name] = workflow

    async def unregister_workflow(self, name: str) -> None:
        """Unregister a workflow.

        Args:
            name: Workflow name
        """
        if name in self._workflows:
            del self._workflows[name]

    async def get_workflow(self, name: str) -> Optional[WorkflowConfig]:
        """Get a workflow by name.

        Args:
            name: Workflow name

        Returns:
            Optional[WorkflowConfig]: Workflow configuration if found
        """
        return self._workflows.get(name)

    async def list_workflows(self) -> List[WorkflowConfig]:
        """List all workflows.

        Returns:
            List[WorkflowConfig]: List of workflow configurations
        """
        return list(self._workflows.values())
