"""Quickstart Example: Task Management Assistant

This example demonstrates building a task management assistant using PepperPy.
It shows how to create a simple agent that processes tasks and manages memory.

Prerequisites:
  - Python 3.12+
  - pip install pepperpy

Quick Start:
  ```bash
  # Install and run
  pip install pepperpy
  python examples/quickstart.py
  ```
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from pepperpy.agents.base import Agent
from pepperpy.common.errors import ProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TaskAssistant(Agent):
    """Task Assistant Agent.

    This agent processes tasks and manages memory for storing task state.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize task assistant.

        Args:
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

    async def process(self, input: str) -> str:
        """Process a task with memory management.

        Args:
            input: Task description

        Returns:
            JSON string containing the task result

        Raises:
            ProcessingError: If task processing fails
        """
        try:
            # Store task start time
            await self.remember("task_start_time", datetime.now().isoformat())

            # Process the task (simplified example)
            result = {
                "task": input,
                "status": "completed",
                "steps": [
                    "Analyzed requirements",
                    "Created execution plan",
                    "Implemented solution",
                ],
                "metrics": {
                    "duration": 1.5,
                    "steps_completed": 3,
                },
            }

            # Store task result
            await self.remember("task_result", result)

            # Return result as JSON string
            return json.dumps(result, indent=2)

        except Exception as e:
            raise ProcessingError(
                f"Failed to process task: {str(e)}",
                details={"task": input},
            ) from e


async def main() -> None:
    """Run quickstart example."""
    logger.info("Starting quickstart example")

    # Create task assistant
    agent = TaskAssistant()
    await agent.initialize()

    try:
        # Process a task
        task = "Create a new project plan"
        logger.info(f"Processing task: {task}")

        # Process task and get result
        result = await agent.process(task)
        logger.info(f"Task result: {result}")

        # Retrieve task state from memory
        start_time = await agent.recall("task_start_time")
        task_result = await agent.recall("task_result")
        logger.info(f"Task state - Start time: {start_time}")
        logger.info(f"Task state - Result: {json.dumps(task_result, indent=2)}")

    except ProcessingError as e:
        logger.error(f"Task processing failed: {e}")
        if e.details:
            logger.error(f"Error details: {e.details}")

    finally:
        # Clean up agent resources
        await agent.cleanup()
        logger.info("Agent cleaned up successfully")


if __name__ == "__main__":
    asyncio.run(main())
