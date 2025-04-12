"""
Testing utilities for A2A providers.

This module provides utilities for testing A2A providers, including
mock implementations and test fixtures.
"""

import uuid
from typing import Any

from pepperpy.a2a.base import (
    A2AProvider,
    AgentCard,
    Message,
    Task,
    TaskState,
    TextPart,
)


class TestAgentCard:
    """Utility for creating test agent cards."""

    @staticmethod
    def create(
        name: str = "Test Agent",
        description: str = "Agent for testing",
        endpoint: str = "http://localhost:8000",
        capabilities: list[str] | None = None,
    ) -> AgentCard:
        """Create a test agent card.

        Args:
            name: Agent name
            description: Agent description
            endpoint: Agent endpoint
            capabilities: Agent capabilities

        Returns:
            Test agent card
        """
        if capabilities is None:
            capabilities = ["text-generation", "testing"]

        return AgentCard(
            name=name,
            description=description,
            endpoint=endpoint,
            capabilities=capabilities,
        )


class TestTask:
    """Utility for creating test tasks."""

    @staticmethod
    def create(
        task_id: str | None = None,
        state: TaskState = TaskState.SUBMITTED,
        messages: list[Message] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a test task.

        Args:
            task_id: Task ID (generated if None)
            state: Task state
            messages: Task messages
            metadata: Task metadata

        Returns:
            Test task
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        if messages is None:
            messages = []

        return Task(
            task_id=task_id,
            state=state,
            messages=messages,
            artifacts=[],
            metadata=metadata or {},
        )

    @staticmethod
    def with_message(
        text: str,
        role: str = "user",
        task_id: str | None = None,
        state: TaskState = TaskState.SUBMITTED,
    ) -> Task:
        """Create a test task with a single text message.

        Args:
            text: Message text
            role: Message role
            task_id: Task ID (generated if None)
            state: Task state

        Returns:
            Test task with a single message
        """
        message = Message(
            role=role,
            parts=[TextPart(text)],
        )

        return TestTask.create(
            task_id=task_id,
            state=state,
            messages=[message],
        )


async def test_provider_lifecycle(provider: A2AProvider) -> None:
    """Test the basic lifecycle of an A2A provider.

    This utility tests initialize -> use -> cleanup for a provider.

    Args:
        provider: A2A provider to test

    Raises:
        AssertionError: If any of the lifecycle tests fail
    """
    # Test initialization
    assert not provider.initialized, "Provider should not be initialized initially"
    await provider.initialize()
    assert provider.initialized, "Provider should be initialized after initialize()"

    # Create a simple task
    agent_id = "test-agent"
    message = Message(role="user", parts=[TextPart("Hello, agent!")])

    # Create and get a task
    task = await provider.create_task(agent_id, message)
    assert task.task_id, "Task should have an ID"
    assert len(task.messages) >= 1, "Task should have at least one message"

    # Get the task
    retrieved_task = await provider.get_task(task.task_id)
    assert retrieved_task.task_id == task.task_id, (
        "Retrieved task should have the same ID"
    )

    # Update the task
    response = Message(role="agent", parts=[TextPart("Hello, user!")])
    updated_task = await provider.update_task(task.task_id, response)
    assert len(updated_task.messages) >= 2, (
        "Updated task should have at least two messages"
    )

    # Clean up
    await provider.cleanup()
    assert not provider.initialized, (
        "Provider should not be initialized after cleanup()"
    )
