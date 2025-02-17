"""Quickstart example for the Pepperpy framework.

This example demonstrates the essential concepts of Pepperpy through a simple
chat-based task assistant that can:
- Understand and process natural language commands
- Remember context across interactions
- Handle basic task management
- Demonstrate proper resource management

Example:
    $ poetry run python examples/quickstart.py

Requirements:
    - Python 3.9+
    - Pepperpy framework
    - OpenAI API key (set as PEPPERPY_API_KEY)

"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from pepperpy.core.base import BaseComponent
from pepperpy.resources import (
    MemoryResource,
    ResourceMetadata,
    ResourceResult,
    ResourceType,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleMemoryResource(MemoryResource):
    """Simple memory resource implementation."""

    def __init__(self, metadata: ResourceMetadata) -> None:
        """Initialize memory resource."""
        super().__init__(metadata=metadata)
        self._data: Dict[str, Any] = {}

    async def _initialize(self) -> None:
        """Initialize the memory store."""
        self._data = {}

    async def _cleanup(self) -> None:
        """Clean up the memory store."""
        self._data.clear()

    async def execute(self, **kwargs: Any) -> ResourceResult[Dict[str, Any]]:
        """Execute memory operations.

        Supports:
        - store: Store a value with a key
        - retrieve: Get a value by key
        - list: List all stored keys
        - clear: Clear all stored data
        """
        operation = kwargs.get("operation")

        if operation == "store":
            key = kwargs.get("key")
            value = kwargs.get("value")
            if key is None or value is None:
                return ResourceResult(
                    success=False,
                    error="Key and value required for store operation",
                )
            self._data[key] = value
            return ResourceResult(success=True, result={"status": "stored"})

        elif operation == "retrieve":
            key = kwargs.get("key")
            if key is None:
                return ResourceResult(
                    success=False,
                    error="Key required for retrieve operation",
                )
            value = self._data.get(key)
            return ResourceResult(success=True, result={"value": value})

        elif operation == "list":
            return ResourceResult(
                success=True,
                result={"keys": list(self._data.keys())},
            )

        elif operation == "clear":
            self._data.clear()
            return ResourceResult(success=True, result={"status": "cleared"})

        return ResourceResult(
            success=False,
            error=f"Unknown operation: {operation}",
        )


class TaskAssistant(BaseComponent):
    """Simple task assistant using Pepperpy."""

    def __init__(self) -> None:
        """Initialize the task assistant."""
        super().__init__(id=uuid4())
        self.memory = SimpleMemoryResource(
            metadata=ResourceMetadata(
                resource_type=ResourceType.MEMORY,
                resource_name="assistant_memory",
                tags=["memory", "context"],
                properties={},
            ),
        )
        self.tasks: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the assistant."""
        logger.info("Initializing task assistant...")
        await self.memory.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up task assistant...")
        await self.memory.cleanup()

    async def process_command(self, command: str) -> str:
        """Process a user command.

        Args:
            command: User command to process

        Returns:
            Response message

        """
        command = command.lower().strip()

        if command == "help":
            return """Available commands:
- add task <description>: Add a new task
- list tasks: Show all tasks
- complete task <number>: Mark a task as complete
- help: Show this help message
- quit: Exit the assistant"""

        elif command.startswith("add task "):
            task = {
                "description": command[9:],
                "created_at": datetime.now(),
                "completed": False,
            }
            self.tasks.append(task)

            # Store task in memory
            await self.memory.execute(
                operation="store",
                key=f"task_{len(self.tasks)}",
                value=task,
            )

            return f"Added task: {task['description']}"

        elif command == "list tasks":
            if not self.tasks:
                return "No tasks found."

            response = "Tasks:\n"
            for i, task in enumerate(self.tasks, 1):
                status = "✓" if task["completed"] else " "
                response += f"{i}. [{status}] {task['description']}\n"
            return response

        elif command.startswith("complete task "):
            try:
                num = int(command[13:]) - 1
                if 0 <= num < len(self.tasks):
                    self.tasks[num]["completed"] = True

                    # Update task in memory
                    await self.memory.execute(
                        operation="store",
                        key=f"task_{num + 1}",
                        value=self.tasks[num],
                    )

                    return f"Marked task {num + 1} as complete."
                return "Invalid task number."
            except ValueError:
                return "Please specify a valid task number."

        else:
            return "Unknown command. Type 'help' for available commands."


async def interactive_session(assistant: TaskAssistant) -> None:
    """Run an interactive session with the task assistant.

    Args:
        assistant: Task assistant instance

    """
    print("\nSimple Task Assistant")
    print("-" * 50)
    print("Type 'help' for available commands or 'quit' to exit.")

    while True:
        try:
            command = input("\nEnter command: ").strip()

            if command.lower() == "quit":
                break

            response = await assistant.process_command(command)
            print("\n" + response)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


async def main() -> None:
    """Run the quickstart example."""
    assistant = TaskAssistant()

    try:
        await assistant.initialize()
        await interactive_session(assistant)
    finally:
        await assistant.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
