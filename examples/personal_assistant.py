"""Personal Assistant Example

This example demonstrates how to create a multi-feature personal assistant using the Pepperpy
framework. The assistant combines multiple capabilities including:
- Task management
- Memory for context retention
- Chat interface
- Calendar integration
- Note-taking

The example shows how to:
1. Initialize and manage multiple capabilities
2. Handle user interactions
3. Maintain context across sessions
4. Integrate with external services
5. Handle errors and cleanup resources

Requirements:
- Python 3.12+
- Pepperpy library

Usage:
    poetry run python examples/personal_assistant.py
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

from pepperpy.core.common.extensions import Extension
from pepperpy.core.common.logging import get_logger
from pepperpy.events import EventBus
from pepperpy.resources import (
    BaseResource,
    MemoryResource,
    ResourceManager,
    ResourceMetadata,
    ResourceType,
    StorageResource,
)

# Configure logging
logger = get_logger(__name__)

# Test data
TEST_TASKS = [
    {
        "title": "Implement task management",
        "description": "Create task management capability with CRUD operations",
    },
    {
        "title": "Add memory integration",
        "description": "Integrate memory resource for context retention",
    },
    {
        "title": "Set up storage",
        "description": "Configure storage resource for file management",
    },
]

TEST_NOTES = [
    {
        "title": "Project Overview",
        "content": "Personal assistant implementation with multiple capabilities",
    },
    {
        "title": "Architecture",
        "content": "Event-driven architecture with resource management",
    },
    {
        "title": "Features",
        "content": "Task management, memory, storage, and event handling",
    },
]

TEST_CALENDAR = [
    {
        "title": "Team Meeting",
        "description": "Weekly team sync",
        "start": "2024-02-21T10:00:00Z",
        "end": "2024-02-21T11:00:00Z",
    },
    {
        "title": "Code Review",
        "description": "Review personal assistant implementation",
        "start": "2024-02-21T14:00:00Z",
        "end": "2024-02-21T15:00:00Z",
    },
    {
        "title": "Planning",
        "description": "Plan next sprint",
        "start": "2024-02-21T16:00:00Z",
        "end": "2024-02-21T17:00:00Z",
    },
]


class PersonalAssistantConfig(BaseModel):
    """Configuration for personal assistant."""

    name: str = "personal_assistant"
    version: str = "1.0.0"
    description: str = "Example personal assistant implementation"


class ExampleMemoryResource(MemoryResource):
    """Example memory resource implementation."""

    def __init__(
        self, metadata: ResourceMetadata, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize memory resource.

        Args:
            metadata: Resource metadata
            event_bus: Optional event bus for resource events
        """
        super().__init__(metadata=metadata, event_bus=event_bus)
        self._data = {}

    async def _initialize(self) -> None:
        """Initialize memory storage."""
        logger.info("Initializing memory resource", extra={"id": str(self.metadata.id)})

    async def _cleanup(self) -> None:
        """Clean up memory storage."""
        logger.info("Cleaning up memory resource", extra={"id": str(self.metadata.id)})
        self._data.clear()

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory operations."""
        if operation == "store":
            self._data[params["key"]] = params["value"]
            return {"status": "success"}
        elif operation == "retrieve":
            value = self._data.get(params["key"])
            return {"status": "success", "value": value}
        raise ValueError(f"Unknown operation: {operation}")


class ExampleStorageResource(StorageResource):
    """Example storage resource implementation."""

    def __init__(
        self, metadata: ResourceMetadata, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize storage resource.

        Args:
            metadata: Resource metadata
            event_bus: Optional event bus for resource events
        """
        super().__init__(metadata=metadata, event_bus=event_bus)
        self._files = {}

    async def _initialize(self) -> None:
        """Initialize storage."""
        logger.info(
            "Initializing storage resource", extra={"id": str(self.metadata.id)}
        )

    async def _cleanup(self) -> None:
        """Clean up storage."""
        logger.info("Cleaning up storage resource", extra={"id": str(self.metadata.id)})
        self._files.clear()

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute storage operations."""
        if operation == "write":
            self._files[params["path"]] = params["content"]
            return {"status": "success"}
        elif operation == "read":
            content = self._files.get(params["path"])
            return {"status": "success", "content": content}
        raise ValueError(f"Unknown operation: {operation}")


class TaskManagementCapability(BaseResource):
    """Task management capability."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """Initialize task management capability.

        Args:
            event_bus: Optional event bus for capability events
        """
        super().__init__(
            metadata=ResourceMetadata(
                resource_type=ResourceType.MEMORY,
                resource_name="task_manager",
                version="1.0.0",
                tags=["task_management"],
                properties={},
            ),
            event_bus=event_bus,
        )
        self._tasks: List[Dict[str, Any]] = []

    async def _initialize(self) -> None:
        """Initialize task management resources."""
        logger.info("Initializing task management", extra={"id": str(self.metadata.id)})

    async def _cleanup(self) -> None:
        """Clean up task management resources."""
        logger.info("Cleaning up task management", extra={"id": str(self.metadata.id)})
        self._tasks.clear()

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task management operation.

        Args:
            operation: Operation to execute
            params: Operation parameters

        Returns:
            Operation result
        """
        if operation == "add_task":
            task = {
                "id": str(uuid4()),
                "title": params["title"],
                "description": params.get("description", ""),
                "created_at": datetime.now(UTC).isoformat(),
                "completed": False,
            }
            self._tasks.append(task)
            return {"status": "success", "task": task}

        elif operation == "list_tasks":
            return {"tasks": self._tasks}

        elif operation == "complete_task":
            task_id = params["task_id"]
            for task in self._tasks:
                if task["id"] == task_id:
                    task["completed"] = True
                    return {"status": "success", "task": task}
            return {"status": "error", "message": "Task not found"}

        return {"status": "error", "message": "Invalid operation"}


class PersonalAssistant(Extension[PersonalAssistantConfig]):
    """Example personal assistant implementation."""

    def __init__(
        self,
        config: Optional[PersonalAssistantConfig] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize personal assistant.

        Args:
            config: Optional configuration
            event_bus: Optional event bus
        """
        super().__init__(
            name="personal_assistant",
            version="1.0.0",
            config=config,
            event_bus=event_bus,
        )
        self._task_manager = TaskManagementCapability(event_bus=event_bus)
        self._resource_manager = ResourceManager(
            name="example_resource_manager",
            version="1.0.0",
            event_bus=event_bus,
        )

        # Initialize memory and storage resources
        self.memory = ExampleMemoryResource(
            metadata=ResourceMetadata(
                resource_type=ResourceType.MEMORY,
                resource_name="assistant_memory",
                version="1.0.0",
                tags=["memory", "context"],
                properties={"storage_type": "memory"},
            ),
            event_bus=event_bus,
        )
        self.storage = ExampleStorageResource(
            metadata=ResourceMetadata(
                resource_type=ResourceType.STORAGE,
                resource_name="assistant_storage",
                version="1.0.0",
                tags=["storage", "files"],
                properties={"storage_type": "local"},
            ),
            event_bus=event_bus,
        )

    async def _initialize(self) -> None:
        """Initialize personal assistant resources."""
        logger.info(
            "Initializing personal assistant", extra={"id": str(self.metadata.id)}
        )
        # Register and initialize capabilities
        await self._resource_manager.register_resource(self._task_manager)
        await self._resource_manager.register_resource(self.memory)
        await self._resource_manager.register_resource(self.storage)

        # Initialize all resources
        for resource in await self._resource_manager.get_resources():
            await resource.initialize()

    async def _cleanup(self) -> None:
        """Clean up personal assistant resources."""
        logger.info(
            "Cleaning up personal assistant", extra={"id": str(self.metadata.id)}
        )
        # Clean up all resources
        for resource in await self._resource_manager.get_resources():
            await resource.cleanup()

    async def process_tasks(self) -> None:
        """Process test tasks."""
        logger.info("Processing tasks")

        # Add tasks
        for task_data in TEST_TASKS:
            result = await self._task_manager.execute("add_task", task_data)
            logger.info(
                "Added task",
                extra={
                    "task_id": result["task"]["id"],
                    "title": result["task"]["title"],
                },
            )

        # List tasks
        result = await self._task_manager.execute("list_tasks", {})
        tasks = result["tasks"]
        logger.info("Listed tasks", extra={"task_count": len(tasks)})

        # Complete first task
        if tasks:
            result = await self._task_manager.execute(
                "complete_task", {"task_id": tasks[0]["id"]}
            )
            logger.info(
                "Completed task",
                extra={
                    "task_id": result["task"]["id"],
                    "title": result["task"]["title"],
                },
            )

        # Print tasks
        print("\nTasks:")
        print("-" * 80)
        for task in tasks:
            status = "✓" if task["completed"] else " "
            print(f"[{status}] {task['title']}: {task['description']}")
        print("-" * 80)

    async def process_notes(self) -> None:
        """Process test notes."""
        logger.info("Processing notes")

        # Store notes
        for note in TEST_NOTES:
            result = await self.storage.execute(
                "write",
                {
                    "path": f"notes/{note['title'].lower().replace(' ', '_')}.txt",
                    "content": note["content"],
                },
            )
            logger.info("Stored note", extra={"title": note["title"]})

        # Read notes
        print("\nNotes:")
        print("-" * 80)
        for note in TEST_NOTES:
            path = f"notes/{note['title'].lower().replace(' ', '_')}.txt"
            result = await self.storage.execute("read", {"path": path})
            print(f"{note['title']}:")
            print(result["content"])
            print("-" * 80)

    async def process_calendar(self) -> None:
        """Process test calendar events."""
        logger.info("Processing calendar events")

        # Store events in memory
        for event in TEST_CALENDAR:
            result = await self.memory.execute(
                "store",
                {
                    "key": f"calendar/{event['title'].lower().replace(' ', '_')}",
                    "value": event,
                },
            )
            logger.info("Stored calendar event", extra={"title": event["title"]})

        # Retrieve events
        print("\nCalendar Events:")
        print("-" * 80)
        for event in TEST_CALENDAR:
            key = f"calendar/{event['title'].lower().replace(' ', '_')}"
            result = await self.memory.execute("retrieve", {"key": key})
            event_data = result["value"]
            print(
                f"{event_data['title']} ({event_data['start']} - {event_data['end']})"
            )
            print(f"Description: {event_data['description']}")
            print("-" * 80)


async def main() -> None:
    """Run the personal assistant example."""
    try:
        # Create and initialize personal assistant
        assistant = PersonalAssistant()
        await assistant.initialize()

        # Process test data
        await assistant.process_tasks()
        await assistant.process_notes()
        await assistant.process_calendar()

        # Clean up
        await assistant.cleanup()

    except Exception as e:
        logger.error("Personal assistant example failed", extra={"error": str(e)})
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
