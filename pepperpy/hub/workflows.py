"""Workflow management for coordinating AI agents.

This module provides classes for defining and executing workflows that
coordinate multiple AI agents to complete complex tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field
from structlog import get_logger

from pepperpy.core.types import Message, MessageType
from pepperpy.hub.session import Session

logger = get_logger()


class WorkflowConfig(BaseModel):
    """Configuration for a workflow.

    Attributes:
        name: Workflow name
        description: Workflow description
        steps: List of workflow steps
        metadata: Optional workflow metadata

    """

    name: str
    description: str = "No description provided"
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Workflow:
    """A workflow that coordinates multiple agents to complete a task.

    Workflows provide:
    - Step-by-step task execution
    - Agent coordination and handoff
    - Progress tracking and monitoring
    - Error handling and recovery
    """

    def __init__(
        self,
        name: str,
        steps: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a workflow."""
        self.name = name
        self.steps = steps
        self.metadata = metadata or {}
        self._client = None

    @classmethod
    async def from_config(cls, client: Any, config_path: Path) -> "Workflow":
        """Load a workflow from a configuration file.

        Args:
            client: The PepperpyClient instance
            config_path: Path to the workflow configuration file

        Returns:
            The loaded workflow instance

        """
        with open(config_path) as f:
            config = yaml.safe_load(f)

        workflow = cls(
            name=config["name"],
            steps=config.get("steps", []),
            metadata=config.get("metadata", {}),
        )
        workflow._client = client
        return workflow

    async def run(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run the workflow on a task.

        Args:
            task: The task to perform
            context: Optional shared context
            **kwargs: Additional task parameters

        Returns:
            The task result

        Example:
            >>> flow = await hub.workflow("research-flow")
            >>> async with flow.run(
            ...     "Research quantum computing",
            ...     context={"depth": "technical"}
            ... ) as session:
            ...     print(f"Progress: {session.progress}%")
            ...     print(f"Current: {session.current_step}")

        """
        if not self._client:
            raise RuntimeError("Workflow not properly initialized with client")

        session = Session(
            task,
            workflow=self.name,
            metadata={"context": context, **kwargs} if context else kwargs,
        )

        async with session.run() as running:
            # Initialize shared context
            shared_context = {
                "task": task,
                "workflow": self.name,
                **(context or {}),
                **kwargs,
            }

            # Execute workflow steps
            result = None
            for step in self.steps:
                step_name = step["name"]
                agent_name = step.get("agent")
                description = step.get("description", f"Running {step_name}")

                # Start step
                running.start_step(
                    name=step_name,
                    description=description,
                    agent=agent_name or "workflow",
                )

                try:
                    # Load agent for step
                    from pepperpy.hub import PepperpyHub

                    if not agent_name or not isinstance(agent_name, str):
                        raise ValueError(f"Invalid agent name in step {step_name}")

                    hub = PepperpyHub(self._client)
                    agent = await hub.agent(agent_name)

                    # Create message with context
                    message = Message(
                        content={
                            "task": task,
                            "context": shared_context,
                            "step": step,
                        },
                        type=MessageType.COMMAND,
                    )

                    # Execute step
                    response = await agent.process_message(message)
                    if isinstance(response.content, dict):
                        step_result = response.content.get("result")
                    else:
                        step_result = response.content

                    # Update shared context
                    shared_context[f"{step_name}_result"] = step_result
                    result = step_result  # Update final result
                    running.complete_step(step_result)

                except Exception as e:
                    running.fail_step(str(e))
                    raise

            return result

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Workflow(name='{self.name}', steps={len(self.steps)})"


__all__ = ["Workflow", "WorkflowConfig"]
