"""Base classes for workflow management.

This module provides base classes and utilities for managing AI workflows.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from pepperpy.hub.agents import Agent


@dataclass
class WorkflowStep:
    """A step in a workflow."""

    name: str
    agent: Agent
    prompt: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


@dataclass
class WorkflowConfig:
    """Configuration for a workflow."""

    name: str
    description: str
    steps: List[WorkflowStep]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


class Workflow:
    """Base class for AI workflows."""

    def __init__(self, config: WorkflowConfig) -> None:
        """Initialize the workflow.

        Args:
        ----
            config: Configuration for the workflow.

        """
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with the given inputs.

        Args:
        ----
            inputs: Input values for the workflow.

        Returns:
        -------
            The workflow's output values.

        """
        current_state = inputs.copy()

        for step in self.config.steps:
            # Format the prompt with current state
            formatted_prompt = step.prompt.format(**current_state)

            # Execute the step
            result = await step.agent.execute(formatted_prompt)

            # Update the state with the step's outputs
            current_state.update(result)

        # Extract and return only the defined outputs
        return {
            key: current_state[key]
            for key in self.config.outputs
            if key in current_state
        }


class WorkflowRegistry:
    """Registry for managing and loading workflows."""

    _workflows: Dict[str, Workflow] = {}

    @classmethod
    def register(cls, name: str, workflow: Workflow) -> None:
        """Register a workflow.

        Args:
        ----
            name: Name to register the workflow under.
            workflow: The workflow instance to register.

        """
        cls._workflows[name] = workflow

    @classmethod
    def get(cls, name: str) -> Workflow:
        """Get a registered workflow by name.

        Args:
        ----
            name: Name of the workflow to get.

        Returns:
        -------
            The registered workflow.

        Raises:
        ------
            KeyError: If no workflow is registered with the given name.

        """
        if name not in cls._workflows:
            raise KeyError(f"No workflow registered with name: {name}")
        return cls._workflows[name]

    @classmethod
    def list(cls) -> Dict[str, Workflow]:
        """List all registered workflows.

        Returns
        -------
            Dictionary of registered workflows.

        """
        return cls._workflows.copy()
