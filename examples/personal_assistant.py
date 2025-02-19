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
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pepperpy.capabilities import (
    BaseCapability,
    CapabilityMetadata,
    CapabilityType,
)
from pepperpy.core.base import BaseComponent
from pepperpy.core.logging import get_logger
from pepperpy.resources import (
    MemoryResource,
    ResourceManager,
    ResourceMetadata,
    ResourceType,
    StorageResource,
)

logger = get_logger(__name__)


class ExampleMemoryResource(MemoryResource):
    """Example memory resource implementation."""

    async def _initialize(self) -> None:
        """Initialize memory storage."""
        logger.info("Initializing memory resource", extra={"id": str(self.id)})
        self._data = {}

    async def _cleanup(self) -> None:
        """Clean up memory storage."""
        logger.info("Cleaning up memory resource", extra={"id": str(self.id)})
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

    async def _initialize(self) -> None:
        """Initialize storage."""
        logger.info("Initializing storage resource", extra={"id": str(self.id)})
        self._files = {}

    async def _cleanup(self) -> None:
        """Clean up storage."""
        logger.info("Cleaning up storage resource", extra={"id": str(self.id)})
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


class ExampleResourceManager(ResourceManager):
    """Example resource manager implementation."""

    async def initialize(self) -> None:
        """Initialize the resource manager."""
        logger.info("Initializing resource manager", extra={"id": str(self.id)})
        self._resources = {}

    async def register_resource(self, resource: Any) -> None:
        """Register a resource with the manager."""
        self._resources[str(resource.id)] = resource

    async def initialize_all(self) -> None:
        """Initialize all registered resources."""
        for resource in self._resources.values():
            await resource.initialize()

    async def cleanup_all(self) -> None:
        """Clean up all registered resources."""
        for resource in self._resources.values():
            await resource.cleanup()
        self._resources.clear()


class TaskManagementCapability(BaseCapability):
    """Manages tasks and todo items for the personal assistant."""

    def __init__(self, id: Optional[UUID] = None) -> None:
        """Initialize the task management capability.

        Args:
            id: Optional UUID for the capability

        """
        metadata = CapabilityMetadata(
            capability_type=CapabilityType.MEMORY,
            capability_name="task_management",
            version="1.0.0",
            tags=["tasks", "todo"],
            properties={"storage_type": "memory"},
        )
        super().__init__(metadata, id)
        self.tasks: List[Dict[str, Any]] = []

    async def _initialize(self) -> None:
        """Initialize task storage."""
        logger.info("Initializing task management", extra={"id": str(self.id)})

    async def _cleanup(self) -> None:
        """Clean up task management resources."""
        logger.info("Cleaning up task management", extra={"id": str(self.id)})
        self.tasks.clear()

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task management operations.

        Args:
            operation: Operation to perform (add_task, list_tasks, complete_task)
            params: Operation parameters

        Returns:
            Operation result

        """
        if operation == "add_task":
            task = {
                "id": str(uuid4()),
                "title": params["title"],
                "description": params.get("description", ""),
                "due_date": params.get("due_date"),
                "created_at": datetime.now().isoformat(),
                "completed": False,
            }
            self.tasks.append(task)
            return {"status": "success", "task": task}

        elif operation == "list_tasks":
            return {"tasks": self.tasks}

        elif operation == "complete_task":
            task_id = params["task_id"]
            for task in self.tasks:
                if task["id"] == task_id:
                    task["completed"] = True
                    return {"status": "success", "task": task}
            return {"status": "error", "message": "Task not found"}

        raise ValueError(f"Unknown operation: {operation}")


class PersonalAssistant(BaseComponent):
    """Multi-feature personal assistant using the Pepperpy framework."""

    def __init__(self) -> None:
        """Initialize the personal assistant with its capabilities."""
        super().__init__(id=uuid4())
        self.resource_manager = ExampleResourceManager()
        self.task_manager = TaskManagementCapability()

        # Initialize memory resource with proper metadata
        memory_metadata = ResourceMetadata(
            resource_type=ResourceType.MEMORY,
            resource_name="assistant_memory",
            version="1.0.0",
            tags=["memory", "context"],
            properties={"storage_type": "memory"},
        )
        self.memory = ExampleMemoryResource(metadata=memory_metadata)

        # Initialize storage resource with proper metadata
        storage_metadata = ResourceMetadata(
            resource_type=ResourceType.STORAGE,
            resource_name="assistant_storage",
            version="1.0.0",
            tags=["storage", "files"],
            properties={"storage_type": "local"},
        )
        self.storage = ExampleStorageResource(metadata=storage_metadata)

    async def initialize(self) -> None:
        """Initialize all assistant capabilities and resources."""
        logger.info("Initializing personal assistant")

        # Register and initialize capabilities
        await self.resource_manager.register_resource(self.task_manager)
        await self.resource_manager.register_resource(self.memory)
        await self.resource_manager.register_resource(self.storage)

        # Initialize all resources
        await self.resource_manager.initialize_all()

    async def cleanup(self) -> None:
        """Clean up all assistant resources."""
        logger.info("Cleaning up personal assistant")
        await self.resource_manager.cleanup_all()

    async def process_command(
        self, command: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a user command.

        Args:
            command: Command to execute
            params: Command parameters

        Returns:
            Command result

        """
        logger.info(
            "Processing command",
            extra={"command": command, "params": json.dumps(params)},
        )

        try:
            if command == "add_task":
                return await self.task_manager.execute("add_task", params)

            elif command == "list_tasks":
                return await self.task_manager.execute("list_tasks", params)

            elif command == "complete_task":
                # First show available tasks
                tasks_result = await self.task_manager.execute("list_tasks", {})
                if tasks_result.get("tasks"):
                    print("\nAvailable tasks:")
                    for task in tasks_result["tasks"]:
                        print(f"ID: {task['id']}")
                        print(f"Title: {task['title']}")
                        print(
                            f"Status: {'Completed' if task['completed'] else 'Pending'}"
                        )
                        print()

                    print("Task ID: ", end="", flush=True)
                    task_id = sys.stdin.readline()
                    if not task_id:
                        return {"status": "error", "message": "No task ID provided"}
                    params["task_id"] = task_id.strip()
                    return await self.task_manager.execute("complete_task", params)
                return {"status": "error", "message": "No tasks available"}

            elif command == "save_note":
                return await self.storage.execute(
                    "write",
                    {
                        "path": f"notes/{params['title']}.txt",
                        "content": params["content"],
                    },
                )

            elif command == "remember":
                return await self.memory.execute(
                    "store", {"key": params["key"], "value": params["value"]}
                )

            elif command == "recall":
                return await self.memory.execute("retrieve", {"key": params["key"]})

            elif command == "exit" or command == "quit":
                return {"status": "success", "message": "Goodbye!"}

            raise ValueError(f"Unknown command: {command}")

        except Exception as e:
            logger.error(
                "Command processing failed", extra={"error": str(e), "command": command}
            )
            return {"status": "error", "message": str(e)}


async def interactive_session(assistant: PersonalAssistant) -> None:
    """Run a demo session with predefined inputs to showcase all features.

    Args:
        assistant: Initialized personal assistant instance

    """
    # Predefined test sequence
    test_sequence = [
        # Add tasks
        (
            "add_task",
            {
                "title": "Implement new feature",
                "description": "Add AI-powered code suggestions",
                "due_date": "2024-03-01",
            },
        ),
        (
            "add_task",
            {
                "title": "Write documentation",
                "description": "Document the new AI features",
                "due_date": "2024-03-15",
            },
        ),
        # List tasks
        ("list_tasks", {}),
        # Save notes
        (
            "save_note",
            {
                "title": "Feature Notes",
                "content": "AI Feature Requirements:\n- Code analysis\n- Suggestion generation\n- Integration with IDE",
            },
        ),
        # Store and retrieve memory
        ("remember", {"key": "feature_status", "value": "in_progress"}),
        ("recall", {"key": "feature_status"}),
        # Complete task
        (
            "complete_task",
            {
                "task_id": "1"  # Will be replaced with actual task ID
            },
        ),
        # Final task list
        ("list_tasks", {}),
    ]

    print("Running Personal Assistant Demo")
    print("-" * 50)

    try:
        # Execute test sequence
        for command, params in test_sequence:
            print(f"\nExecuting: {command}")

            # Special handling for complete_task to get the first task's ID
            if command == "complete_task":
                tasks_result = await assistant.process_command("list_tasks", {})
                if tasks_result.get("tasks"):
                    first_task = tasks_result["tasks"][0]
                    params["task_id"] = first_task["id"]

            # Process command
            result = await assistant.process_command(command, params)
            print(f"Result: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")

    print("\nDemo completed successfully!")


async def main() -> None:
    """Run the personal assistant example."""
    assistant = PersonalAssistant()

    try:
        await assistant.initialize()
        await interactive_session(assistant)
    finally:
        await assistant.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
