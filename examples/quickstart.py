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
import sys
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from pepperpy.core.base import BaseComponent
from pepperpy.memory.base import BaseMemory
from pepperpy.memory.types import (
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemoryType,
)
from pepperpy.memory.types import (
    MemoryResult as MemorySearchResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleMemory(BaseMemory[str, Dict[str, Any]]):
    """Simple memory implementation."""

    def __init__(self) -> None:
        """Initialize memory."""
        self._data: Dict[str, Dict[str, Any]] = {}

    async def store(
        self,
        key: str,
        value: Dict[str, Any],
        type: str = MemoryType.SHORT_TERM,
        scope: str = MemoryScope.SESSION,
        metadata: Dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        indices: set[str] | None = None,
    ) -> MemoryEntry[Dict[str, Any]]:
        """Store a value in memory."""
        entry = MemoryEntry(
            key=key,
            value=value,
            type=type,
            scope=scope,
            metadata=metadata or {},
            expires_at=expires_at,
        )
        self._data[key] = value
        return entry

    async def retrieve(
        self,
        key: str,
        type: str | None = None,
    ) -> MemoryEntry[Dict[str, Any]]:
        """Retrieve a value from memory."""
        value = self._data.get(key)
        if value is None:
            raise KeyError(f"Key not found: {key}")
        return MemoryEntry(
            key=key,
            value=value,
            type=type or MemoryType.SHORT_TERM,
            scope=MemoryScope.SESSION,
        )

    async def search(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Search memory (not implemented)."""
        raise NotImplementedError("Search not implemented")

    async def similar(
        self,
        key: str,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Find similar entries (not implemented)."""
        raise NotImplementedError("Similar not implemented")

    async def cleanup_expired(self) -> int:
        """Clean up expired entries (not implemented)."""
        return 0


class TaskAssistant(BaseComponent):
    """Simple task assistant using Pepperpy."""

    def __init__(self) -> None:
        """Initialize the task assistant."""
        super().__init__(id=uuid4())
        self.memory = SimpleMemory()
        self.tasks: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the assistant."""
        logger.info("Initializing task assistant...")
        # Memory is initialized on creation

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up task assistant...")
        # Store final state in memory
        await self.memory.store(
            "tasks",
            {"tasks": self.tasks},
            type=MemoryType.LONG_TERM,
            scope=MemoryScope.GLOBAL,
        )

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
                "created_at": datetime.now().isoformat(),
                "completed": False,
            }
            self.tasks.append(task)
            # Store in memory
            await self.memory.store(
                f"task_{len(self.tasks)}",
                task,
                type=MemoryType.SHORT_TERM,
                scope=MemoryScope.SESSION,
            )
            return f"Added task: {task['description']}"

        elif command == "list tasks":
            if not self.tasks:
                return "No tasks found"

            task_list = []
            for i, task in enumerate(self.tasks, 1):
                status = "✓" if task["completed"] else " "
                task_list.append(f"{i}. [{status}] {task['description']}")
            return "\n".join(task_list)

        elif command.startswith("complete task "):
            try:
                task_num = int(command[13:]) - 1
                if 0 <= task_num < len(self.tasks):
                    self.tasks[task_num]["completed"] = True
                    # Update in memory
                    await self.memory.store(
                        f"task_{task_num + 1}",
                        self.tasks[task_num],
                        type=MemoryType.SHORT_TERM,
                        scope=MemoryScope.SESSION,
                    )
                    return f"Marked task {task_num + 1} as complete"
                return "Invalid task number"
            except ValueError:
                return "Invalid task number format"

        return "Unknown command. Type 'help' for available commands."


async def main() -> None:
    """Run the example."""
    logger.info("Initializing task assistant...")
    assistant = TaskAssistant()
    await assistant.initialize()

    try:
        # Check if we should run in automated test mode
        if "--test" in sys.argv:
            # Run automated test sequence
            test_commands = [
                "help",
                "add task Write documentation",
                "add task Review code",
                "add task Deploy application",
                "list tasks",
                "complete task 1",
                "list tasks",
                "quit",
            ]

            print("Welcome to the Task Assistant!")
            print("Running in automated test mode...")
            print()

            for command in test_commands:
                print(f"Command: {command}")
                if command == "quit":
                    break
                response = await assistant.process_command(command)
                print(response)
                print()
        else:
            # Interactive mode
            print("Welcome to the Task Assistant!")
            print("Type 'help' for available commands or 'quit' to exit.")
            print()

            while True:
                command = input("Enter command: ").strip()
                if command == "quit":
                    break
                response = await assistant.process_command(command)
                print(response)
                print()

    finally:
        await assistant.cleanup()
        logger.info("Task assistant terminated")


if __name__ == "__main__":
    asyncio.run(main())
