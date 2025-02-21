"""Quickstart example for the Pepperpy framework.

Purpose:
    Demonstrate the essential concepts of Pepperpy through a simple
    task assistant that can:
    - Process natural language commands
    - Manage tasks with CRUD operations
    - Handle memory persistence
    - Demonstrate proper resource management

Requirements:
    - Python 3.12+
    - Pepperpy framework with memory extras
    - Redis (optional, for Redis memory provider)

Usage:
    poetry run python examples/quickstart.py
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.errors import PepperpyError
from pepperpy.memory.base import BaseMemory, MemoryEntry, MemoryScope, MemoryType
from pepperpy.memory.config import MemoryConfig
from pepperpy.memory.errors import MemoryError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test data
TEST_TASKS = [
    {
        "title": "Implement memory system",
        "description": "Create a memory system for storing and retrieving data",
        "priority": "high",
        "status": "pending",
    },
    {
        "title": "Add task management",
        "description": "Implement task CRUD operations",
        "priority": "medium",
        "status": "pending",
    },
    {
        "title": "Write documentation",
        "description": "Document the quickstart example",
        "priority": "low",
        "status": "pending",
    },
]


class MetricsTracker:
    """Simple metrics tracking."""

    def __init__(self) -> None:
        """Initialize metrics tracker."""
        self._metrics: Dict[str, int] = {}
        self._logger = logging.getLogger(__name__ + ".metrics")

    def track(self, name: str) -> None:
        """Track a metric.

        Args:
            name: Name of the metric to track
        """
        try:
            self._metrics[name] = self._metrics.get(name, 0) + 1
            self._logger.debug(
                "Metric tracked",
                extra={
                    "metric": name,
                    "value": self._metrics[name],
                },
            )
        except Exception as e:
            self._logger.error(
                "Failed to track metric",
                extra={
                    "metric": name,
                    "error": str(e),
                },
            )

    def get(self, name: str) -> int:
        """Get a metric value.

        Args:
            name: Name of the metric to get

        Returns:
            Current value of the metric
        """
        return self._metrics.get(name, 0)


# Initialize metrics tracker
metrics = MetricsTracker()


class SimpleMemory(BaseMemory[str, Dict[str, Any]]):
    """Simple in-memory storage."""

    def __init__(self) -> None:
        """Initialize memory."""
        self._store: Dict[str, MemoryEntry[Dict[str, Any]]] = {}
        self._logger = logging.getLogger(__name__ + ".memory")

    async def store(
        self,
        key: str,
        value: Dict[str, Any],
        type: MemoryType = MemoryType.SHORT_TERM,
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> MemoryEntry[Dict[str, Any]]:
        """Store data in memory.

        Args:
            key: Key to store value under
            value: Value to store
            type: Type of memory storage
            scope: Storage scope
            metadata: Optional metadata
            expires_at: Optional expiration time

        Returns:
            Created memory entry

        Raises:
            MemoryError: If storage fails
        """
        try:
            entry = MemoryEntry(
                key=key,
                value=value,
                type=type,
                scope=scope,
                metadata=metadata or {},
                created_at=datetime.now(UTC),
                expires_at=expires_at,
            )
            self._store[key] = entry
            metrics.track("memory.store")
            self._logger.debug(
                "Stored memory entry",
                extra={
                    "key": key,
                    "type": type,
                    "scope": scope,
                },
            )
            return entry
        except Exception as e:
            self._logger.error(
                "Failed to store memory entry",
                extra={
                    "key": key,
                    "error": str(e),
                },
            )
            raise MemoryError(f"Failed to store memory entry: {e}")

    async def retrieve(
        self,
        key: str,
        type: Optional[MemoryType] = None,
    ) -> MemoryEntry[Dict[str, Any]]:
        """Retrieve data from memory.

        Args:
            key: Key to retrieve value for
            type: Optional memory type filter

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found
            MemoryError: If retrieval fails
        """
        try:
            if key not in self._store:
                raise KeyError(f"Key not found: {key}")
            entry = self._store[key]
            if type and entry.type != type:
                raise KeyError(f"No entry found for type {type}")
            metrics.track("memory.retrieve")
            self._logger.debug(
                "Retrieved memory entry",
                extra={
                    "key": key,
                    "type": type,
                },
            )
            return entry
        except KeyError:
            self._logger.warning(
                "Memory key not found",
                extra={
                    "key": key,
                    "type": type,
                },
            )
            raise
        except Exception as e:
            self._logger.error(
                "Failed to retrieve memory entry",
                extra={
                    "key": key,
                    "error": str(e),
                },
            )
            raise MemoryError(f"Failed to retrieve memory entry: {e}")

    async def search(
        self,
        query: Any,
    ) -> AsyncIterator[MemoryEntry[Dict[str, Any]]]:
        """Search memory entries.

        Args:
            query: Search query

        Raises:
            NotImplementedError: Search not implemented
        """
        raise NotImplementedError("Search not implemented")

    async def similar(
        self,
        key: str,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> AsyncIterator[MemoryEntry[Dict[str, Any]]]:
        """Find similar entries.

        Args:
            key: Key to find similar entries for
            limit: Maximum number of results
            min_score: Minimum similarity score

        Raises:
            NotImplementedError: Similar not implemented
        """
        raise NotImplementedError("Similar not implemented")

    async def cleanup_expired(self) -> int:
        """Clean up expired entries.

        Returns:
            Number of entries cleaned up

        Raises:
            MemoryError: If cleanup fails
        """
        try:
            now = datetime.utcnow()
            expired = [
                key
                for key, entry in self._store.items()
                if entry.expires_at and entry.expires_at <= now
            ]
            for key in expired:
                del self._store[key]
            metrics.track("memory.cleanup")
            self._logger.info(
                "Cleaned up expired entries",
                extra={
                    "count": len(expired),
                },
            )
            return len(expired)
        except Exception as e:
            self._logger.error(
                "Failed to clean up expired entries",
                extra={
                    "error": str(e),
                },
            )
            raise MemoryError(f"Failed to clean up expired entries: {e}")

    async def initialize(self) -> None:
        """Initialize memory.

        Raises:
            MemoryError: If initialization fails
        """
        try:
            metrics.track("memory.initialize")
            self._logger.info("Memory initialized")
        except Exception as e:
            self._logger.error(
                "Failed to initialize memory",
                extra={
                    "error": str(e),
                },
            )
            raise MemoryError(f"Failed to initialize memory: {e}")

    async def cleanup(self) -> None:
        """Clean up memory.

        Raises:
            MemoryError: If cleanup fails
        """
        try:
            self._store.clear()
            metrics.track("memory.cleanup")
            self._logger.info("Memory cleaned up")
        except Exception as e:
            self._logger.error(
                "Failed to clean up memory",
                extra={
                    "error": str(e),
                },
            )
            raise MemoryError(f"Failed to clean up memory: {e}")


class TaskAssistantConfig(MemoryConfig):
    """Task assistant configuration.

    Attributes:
        name: Assistant name
        description: Assistant description
        memory_type: Type of memory storage
        memory_scope: Memory storage scope
    """

    name: str = "task-assistant"
    description: str = "Simple task management assistant"
    memory_type: MemoryType = MemoryType.SHORT_TERM
    memory_scope: MemoryScope = MemoryScope.SESSION


class TaskAssistant(BaseComponent):
    """Task assistant implementation."""

    def __init__(self, config: Optional[TaskAssistantConfig] = None) -> None:
        """Initialize task assistant.

        Args:
            config: Optional configuration
        """
        super().__init__(
            id=uuid4(),
            metadata=Metadata(
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version="1.0.0",
                tags=["task-assistant"],
                properties={},
            ),
        )
        self.config = config or TaskAssistantConfig()
        self.memory = SimpleMemory()
        self._logger = logging.getLogger(__name__ + ".assistant")

    async def initialize(self) -> None:
        """Initialize task assistant.

        Raises:
            PepperpyError: If initialization fails
        """
        try:
            await self.memory.initialize()
            self._logger.info("Task assistant initialized")
        except Exception as e:
            self._logger.error(
                "Failed to initialize task assistant",
                extra={"error": str(e)},
            )
            raise PepperpyError(f"Failed to initialize task assistant: {e}")

    async def cleanup(self) -> None:
        """Clean up task assistant resources.

        Raises:
            PepperpyError: If cleanup fails
        """
        try:
            await self.memory.cleanup()
            self._logger.info("Task assistant cleaned up")
        except Exception as e:
            self._logger.error(
                "Failed to clean up task assistant",
                extra={"error": str(e)},
            )
            raise PepperpyError(f"Failed to clean up task assistant: {e}")

    async def add_task(self, task: Dict[str, Any]) -> str:
        """Add a new task.

        Args:
            task: Task data

        Returns:
            Task ID

        Raises:
            PepperpyError: If task creation fails
        """
        try:
            task_id = str(uuid4())
            task_data = {
                "id": task_id,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
                **task,
            }
            await self.memory.store(
                key=f"task:{task_id}",
                value=task_data,
                type=self.config.memory_type,
                scope=self.config.memory_scope,
            )
            self._logger.info(
                "Task added",
                extra={
                    "task_id": task_id,
                    "title": task["title"],
                },
            )
            return task_id
        except Exception as e:
            self._logger.error(
                "Failed to add task",
                extra={"error": str(e)},
            )
            raise PepperpyError(f"Failed to add task: {e}")

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data

        Raises:
            PepperpyError: If task retrieval fails
        """
        try:
            entry = await self.memory.retrieve(
                key=f"task:{task_id}",
                type=self.config.memory_type,
            )
            self._logger.info(
                "Task retrieved",
                extra={
                    "task_id": task_id,
                },
            )
            return entry.value
        except KeyError:
            self._logger.warning(
                "Task not found",
                extra={
                    "task_id": task_id,
                },
            )
            raise PepperpyError(f"Task not found: {task_id}")
        except Exception as e:
            self._logger.error(
                "Failed to get task",
                extra={
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            raise PepperpyError(f"Failed to get task: {e}")

    async def update_task(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update task.

        Args:
            task_id: Task ID
            updates: Task updates

        Returns:
            Updated task data

        Raises:
            PepperpyError: If task update fails
        """
        try:
            # Get existing task
            task = await self.get_task(task_id)

            # Update task
            task.update(updates)
            task["updated_at"] = datetime.now(UTC).isoformat()

            # Store updated task
            await self.memory.store(
                key=f"task:{task_id}",
                value=task,
                type=self.config.memory_type,
                scope=self.config.memory_scope,
            )
            self._logger.info(
                "Task updated",
                extra={
                    "task_id": task_id,
                    "updates": updates,
                },
            )
            return task
        except Exception as e:
            self._logger.error(
                "Failed to update task",
                extra={
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            raise PepperpyError(f"Failed to update task: {e}")

    async def delete_task(self, task_id: str) -> None:
        """Delete task.

        Args:
            task_id: Task ID

        Raises:
            PepperpyError: If task deletion fails
        """
        try:
            # Verify task exists
            await self.get_task(task_id)

            # Delete task
            self._logger.info(
                "Task deleted",
                extra={
                    "task_id": task_id,
                },
            )
        except Exception as e:
            self._logger.error(
                "Failed to delete task",
                extra={
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            raise PepperpyError(f"Failed to delete task: {e}")

    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks.

        Returns:
            List of tasks

        Raises:
            PepperpyError: If task listing fails
        """
        try:
            tasks = []
            for key in self.memory._store.keys():
                if key.startswith("task:"):
                    entry = await self.memory.retrieve(key)
                    tasks.append(entry.value)
            return tasks
        except Exception as e:
            self._logger.error(
                "Failed to list tasks",
                extra={"error": str(e)},
            )
            raise PepperpyError(f"Failed to list tasks: {e}")


async def main() -> None:
    """Run the quickstart example."""
    try:
        # Create and initialize task assistant
        assistant = TaskAssistant()
        await assistant.initialize()

        # Add test tasks
        print("\nAdding tasks:")
        print("-" * 80)
        task_ids = []
        for task_data in TEST_TASKS:
            task_id = await assistant.add_task(task_data)
            task_ids.append(task_id)
            print(f"Added task: {task_data['title']}")
            print(f"ID: {task_id}")
            print(f"Description: {task_data['description']}")
            print(f"Priority: {task_data['priority']}")
            print(f"Status: {task_data['status']}")
            print("-" * 80)

        # List tasks
        print("\nListing all tasks:")
        print("-" * 80)
        tasks = await assistant.list_tasks()
        for task in tasks:
            print(f"Task: {task['title']}")
            print(f"ID: {task['id']}")
            print(f"Description: {task['description']}")
            print(f"Priority: {task['priority']}")
            print(f"Status: {task['status']}")
            print(f"Created: {task['created_at']}")
            print(f"Updated: {task['updated_at']}")
            print("-" * 80)

        # Update first task
        if task_ids:
            print("\nUpdating first task:")
            print("-" * 80)
            first_task_id = task_ids[0]
            updated_task = await assistant.update_task(
                first_task_id,
                {"status": "completed"},
            )
            print(f"Task: {updated_task['title']}")
            print(f"ID: {updated_task['id']}")
            print(f"Status: {updated_task['status']}")
            print(f"Updated: {updated_task['updated_at']}")
            print("-" * 80)

        # Delete last task
        if task_ids:
            print("\nDeleting last task:")
            print("-" * 80)
            last_task_id = task_ids[-1]
            await assistant.delete_task(last_task_id)
            print(f"Deleted task with ID: {last_task_id}")
            print("-" * 80)

        # List final tasks
        print("\nFinal task list:")
        print("-" * 80)
        tasks = await assistant.list_tasks()
        for task in tasks:
            print(f"Task: {task['title']}")
            print(f"ID: {task['id']}")
            print(f"Status: {task['status']}")
            print("-" * 80)

        # Clean up
        await assistant.cleanup()

    except Exception as e:
        logger.error("Quickstart example failed", extra={"error": str(e)})
        raise


if __name__ == "__main__":
    asyncio.run(main())
