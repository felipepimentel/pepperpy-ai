"""Example workflow implementation.

Demonstrates basic workflow functionality.
"""

from pepperpy.workflows.base import (
    BaseWorkflow,
    WorkflowDefinition,
    WorkflowStep,
)


class HelloStep(WorkflowStep):
    """Simple hello step."""

    async def execute(self) -> str:
        """Execute hello step.

        Returns:
            Hello message
        """
        return "Hello"


class WorldStep(WorkflowStep):
    """Simple world step."""

    async def execute(self) -> str:
        """Execute world step.

        Returns:
            World message
        """
        return "World"


class HelloWorldWorkflow(BaseWorkflow):
    """Simple hello world workflow."""

    def __init__(self) -> None:
        """Initialize hello world workflow."""
        definition = WorkflowDefinition("hello_world")
        definition.add_step(HelloStep("hello"))
        definition.add_step(WorldStep("world"))
        super().__init__(definition)
