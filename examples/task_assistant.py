"""Task Assistant Example

This example demonstrates how to use the TaskAssistant agent to manage and execute tasks.
It shows:
1. Creating an agent from Hub configuration
2. Using memory to store task state
3. Processing tasks through a workflow
4. Error handling and cleanup

Requirements:
    pip install pepperpy

Usage:
    python task_assistant.py
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Dict, Optional, Union

from pepperpy.agents.task_assistant import TaskAssistant
from pepperpy.core.common.errors import ProcessingError
from pepperpy.core.common.messages import ProviderMessage, ProviderResponse
from pepperpy.core.common.providers.base import BaseProvider, ProviderConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Mock data for examples
MOCK_TASKS = [
    "Analyze code performance in user authentication module",
    "Update API documentation for new endpoints",
    "Optimize database queries in reporting service",
]

MOCK_WORKFLOW = [
    {
        "step": "plan",
        "description": "Create detailed execution plan",
        "timeout": 5,
    },
    {
        "step": "execute",
        "description": "Execute plan with monitoring",
        "timeout": 10,
    },
    {
        "step": "validate",
        "description": "Validate results and collect metrics",
        "timeout": 5,
    },
]


# Mock provider for testing
class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider."""
        config = ProviderConfig(
            type="mock",
            config=kwargs,
        )
        super().__init__(config=config)

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True
        logger.info("Mock provider initialized")

    async def cleanup(self) -> None:
        """Clean up provider."""
        self._initialized = False
        logger.info("Mock provider cleaned up")

    async def validate(self) -> None:
        """Validate provider configuration."""
        pass

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message."""
        return ProviderResponse(
            content="Task processed successfully",
            metadata={"provider_type": "mock"},
            provider_type="mock",
        )

    async def remember(self, key: str, value: Any) -> None:
        """Mock memory storage."""
        logger.info(f"Storing {key}: {value}")

    async def recall(self, key: str) -> Optional[Any]:
        """Mock memory retrieval."""
        value = f"mock_{key}"
        logger.info(f"Retrieving {key}: {value}")
        return value


async def run_task_example() -> None:
    """Run task assistant example."""
    logger.info("Starting task assistant example")

    # Create agent with workflow and mock provider
    agent = TaskAssistant(
        workflow=MOCK_WORKFLOW,
        provider=MockProvider(),
        memory={
            "enabled": True,
            "type": "simple",
            "config": {
                "auto_cleanup": True,
                "cleanup_interval": 1800,
                "max_entries": 100,
                "default_expiration": 3600,
            },
        },
    )
    await agent.initialize()

    try:
        # Process each mock task
        for task in MOCK_TASKS:
            logger.info(f"Processing task: {task}")

            # Store task context
            await agent.remember("task_start_time", datetime.now().isoformat())
            await agent.remember("task_priority", "high")

            # Process task
            result = await agent.process(task)
            logger.info(f"Task result: {result}")

            # Retrieve and log task state
            start_time = await agent.recall("task_start_time")
            priority = await agent.recall("task_priority")
            logger.info(
                f"Task context - Start time: {start_time}, Priority: {priority}"
            )

    except ProcessingError as e:
        logger.error(f"Task processing failed: {e}")
        if e.details:
            logger.error(f"Error details: {e.details}")

    finally:
        # Clean up agent resources
        await agent.cleanup()
        logger.info("Agent cleaned up successfully")


async def run_workflow_example() -> None:
    """Run workflow customization example."""
    logger.info("Starting workflow example")

    # Create agent with custom workflow and mock provider
    agent = TaskAssistant(
        workflow=MOCK_WORKFLOW,
        provider=MockProvider(),
        memory={
            "enabled": True,
            "type": "simple",
            "config": {
                "auto_cleanup": True,
                "cleanup_interval": 1800,
                "max_entries": 100,
                "default_expiration": 3600,
            },
        },
    )
    await agent.initialize()

    try:
        task = "Optimize database queries for better performance"
        logger.info(f"Processing task with custom workflow: {task}")

        result = await agent.process(task)
        logger.info(f"Task completed: {result}")

    except ProcessingError as e:
        logger.error(f"Workflow execution failed: {e}")

    finally:
        await agent.cleanup()


async def run_memory_example() -> None:
    """Run memory management example."""
    logger.info("Starting memory example")

    # Configure agent with custom memory settings and mock provider
    memory_config: Dict[str, Any] = {
        "memory": {
            "enabled": True,
            "type": "simple",
            "config": {
                "auto_cleanup": True,
                "cleanup_interval": 1800,  # 30 minutes
                "max_entries": 100,
                "default_expiration": 3600,  # 1 hour
            },
        },
    }

    agent = TaskAssistant(
        workflow=MOCK_WORKFLOW, provider=MockProvider(), **memory_config
    )
    await agent.initialize()

    try:
        # Store task context
        await agent.remember("task_priority", "high")
        await agent.remember("task_deadline", "2024-03-01")

        # Process task with context
        task = "Review and update API documentation"
        logger.info(f"Processing task with context: {task}")

        # Retrieve task context
        priority = await agent.recall("task_priority")
        deadline = await agent.recall("task_deadline")
        logger.info(f"Task context - Priority: {priority}, Deadline: {deadline}")

        result = await agent.process(task)
        logger.info(f"Task completed: {result}")

    finally:
        await agent.cleanup()


async def main() -> None:
    """Run all examples."""
    # Run examples
    logger.info("Running task assistant examples")

    await run_task_example()
    logger.info("Task example completed")

    await run_workflow_example()
    logger.info("Workflow example completed")

    await run_memory_example()
    logger.info("Memory example completed")

    logger.info("All examples completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
