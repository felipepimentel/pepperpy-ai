"""Example workflow implementation.

Demonstrates basic workflow functionality.
"""

from pepperpy.workflows.base import (
    BaseWorkflow,
    WorkflowDefinition,
    WorkflowState,
    WorkflowStep,
)


class HelloStep(WorkflowStep):
    """Simple hello step."""

    def __init__(self, id: str):
        """Initialize hello step.

        Args:
            id: Step ID
        """
        super().__init__(
            id=id,
            name="hello_step",
            action="say_hello",
        )


class WorldStep(WorkflowStep):
    """Simple world step."""

    def __init__(self, id: str):
        """Initialize world step.

        Args:
            id: Step ID
        """
        super().__init__(
            id=id,
            name="world_step",
            action="say_world",
        )


class HelloWorldWorkflow(BaseWorkflow):
    """Simple hello world workflow.

    This workflow demonstrates the basic workflow functionality
    by executing two steps in sequence and combining their results.
    """

    def __init__(self) -> None:
        """Initialize workflow."""
        definition = WorkflowDefinition("hello_world")
        definition.add_step(HelloStep("hello"))
        definition.add_step(WorldStep("world"))
        super().__init__(definition)

    async def execute(self) -> str:
        """Execute workflow.

        Returns:
            Combined result of hello and world steps

        Raises:
            WorkflowError: If execution fails
        """
        # This is a simplified implementation for the example
        # In a real workflow, you would use the proper workflow execution mechanisms
        return "Hello World!"
