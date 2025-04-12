"""
Mock implementation of A2A provider for testing and development.

This provider simulates A2A protocol interactions without requiring
external services or network connections.
"""

import asyncio
import uuid
from typing import Any, ClassVar

from pepperpy.a2a import register_provider
from pepperpy.a2a.base import (
    A2AError,
    A2AProvider,
    AgentCard,
    Message,
    Task,
    TaskState,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugin import ProviderPlugin

logger = get_logger(__name__)


class MockA2AError(A2AError):
    """Exceptions related to Mock A2A provider."""

    pass


class MockA2AProvider(A2AProvider, ProviderPlugin):
    """Mock implementation of A2A provider.

    This provider simulates A2A interactions for testing purposes.
    It stores all state in-memory and doesn't require external services.
    """

    # Class variables to store state
    _agents: ClassVar[dict[str, AgentCard]] = {}
    _tasks: ClassVar[dict[str, Task]] = {}

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the mock A2A provider.

        Args:
            config: Optional provider configuration
        """
        super().__init__(config or {})
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if the key is not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def has_config(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Configuration key

        Returns:
            True if the key exists, False otherwise
        """
        return key in self.config

    def update_config(self, **kwargs: Any) -> None:
        """Update the configuration.

        Args:
            **kwargs: Configuration values to update
        """
        self.config.update(kwargs)

    async def _initialize_resources(self) -> None:
        """Initialize mock provider resources."""
        self._logger.info("Initializing Mock A2A Provider")
        # Nothing to initialize for mock provider

    async def _cleanup_resources(self) -> None:
        """Clean up mock provider resources."""
        self._logger.info("Cleaning up Mock A2A Provider")
        # Clear state when requested
        if self.config.get("clear_on_cleanup", False):
            self._logger.debug("Clearing all Mock A2A Provider state")
            self.__class__._agents.clear()
            self.__class__._tasks.clear()

    async def register_agent(self, agent_card: AgentCard) -> str:
        """Register an agent with the provider.

        Args:
            agent_card: Agent card to register

        Returns:
            Agent ID
        """
        agent_id = str(uuid.uuid4())
        self._logger.info(f"Registering agent {agent_id}: {agent_card.name}")
        self.__class__._agents[agent_id] = agent_card
        return agent_id

    async def get_agent(self, agent_id: str) -> AgentCard | None:
        """Get agent information.

        Args:
            agent_id: Agent ID

        Returns:
            Agent card if found, None otherwise
        """
        return self.__class__._agents.get(agent_id)

    async def create_task(self, agent_id: str, message: Message) -> Task:
        """Create a new task for an agent.

        Args:
            agent_id: Target agent ID
            message: Initial message

        Returns:
            Created task

        Raises:
            ValueError: If the agent doesn't exist
        """
        if agent_id not in self.__class__._agents:
            self._logger.error(f"Agent {agent_id} not found")
            raise ValueError(f"Agent {agent_id} not found")

        task_id = str(uuid.uuid4())
        self._logger.info(f"Creating task {task_id} for agent {agent_id}")

        task = Task(
            task_id=task_id,
            state=TaskState.SUBMITTED,
            messages=[message],
            metadata={"agent_id": agent_id},
        )

        self.__class__._tasks[task_id] = task

        # Simulate async processing
        if not self.config.get("disable_task_processing", False):
            asyncio.create_task(self._process_task(task_id))

        return task

    async def get_task(self, task_id: str) -> Task:
        """Get task information.

        Args:
            task_id: Task ID

        Returns:
            Task information

        Raises:
            ValueError: If the task doesn't exist
        """
        if task_id not in self.__class__._tasks:
            self._logger.error(f"Task {task_id} not found")
            raise ValueError(f"Task {task_id} not found")

        return self.__class__._tasks[task_id]

    async def update_task(self, task_id: str, message: Message) -> Task:
        """Update a task with a new message.

        Args:
            task_id: Task ID
            message: New message to add

        Returns:
            Updated task

        Raises:
            ValueError: If the task doesn't exist
        """
        if task_id not in self.__class__._tasks:
            self._logger.error(f"Task {task_id} not found")
            raise ValueError(f"Task {task_id} not found")

        task = self.__class__._tasks[task_id]
        task.messages.append(message)
        self._logger.info(f"Added message to task {task_id}")

        # Update task in simulated processing
        if not self.config.get("disable_task_processing", False):
            asyncio.create_task(self._process_task(task_id))

        return task

    async def _process_task(self, task_id: str) -> None:
        """Simulate task processing.

        Args:
            task_id: Task ID to process
        """
        # Simulate delay
        await asyncio.sleep(self.config.get("processing_delay", 1))

        if task_id not in self.__class__._tasks:
            return

        task = self.__class__._tasks[task_id]
        self._logger.debug(f"Processing task {task_id}")

        # Simulate state transitions
        if task.state == TaskState.SUBMITTED:
            task.state = TaskState.WORKING
            self.__class__._tasks[task_id] = task
            self._logger.debug(f"Task {task_id} state: {task.state}")

            # Simulate more processing time
            await asyncio.sleep(self.config.get("working_delay", 2))

            if task_id not in self.__class__._tasks:
                return

            # Transition to completed
            task = self.__class__._tasks[task_id]
            task.state = TaskState.COMPLETED
            self.__class__._tasks[task_id] = task
            self._logger.debug(f"Task {task_id} state: {task.state}")


@register_provider("mock")
async def create_mock_provider(**kwargs: Any) -> MockA2AProvider:
    """Create a mock A2A provider.

    Args:
        **kwargs: Provider configuration

    Returns:
        Initialized MockA2AProvider instance
    """
    provider = MockA2AProvider(kwargs)
    await provider.initialize()
    return provider
