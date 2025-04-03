"""Example demonstrating the complete PepperPy plugin system.

This example shows how all the plugin system components work together:
- Resource management
- Dependency management
- Event system
- Service integration
"""

import asyncio
from enum import Enum
from typing import Any

from pepperpy.plugins import (
    DependencyType,
    EventContext,
    EventPriority,
    PepperpyPlugin,
    ProviderPlugin,
    ResourceType,
)
from pepperpy.plugins.services import ServiceScope, call_service, service


# Define custom event types
class AppEventType(Enum):
    """Custom application event types."""

    TASK_CREATED = "app.task.created"
    TASK_UPDATED = "app.task.updated"
    TASK_COMPLETED = "app.task.completed"
    FILE_UPLOADED = "app.file.uploaded"
    FILE_PROCESSED = "app.file.processed"


# Base storage plugin that provides storage services
class StoragePlugin(ProviderPlugin):
    """A plugin that provides storage services."""

    __metadata__ = {
        "name": "storage",
        "version": "1.0.0",
        "description": "Storage services plugin",
        "author": "PepperPy Team",
        "provider_type": "storage",
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.items = {}

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register storage as a resource
        self.register_resource(
            resource_key="items",
            resource=self.items,
            resource_type=ResourceType.MEMORY,
            metadata={"description": "Storage items"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    # Storage services

    @service("store", scope=ServiceScope.PUBLIC)
    def store_item(self, key: str, value: Any) -> bool:
        """Store an item.

        Args:
            key: Item key
            value: Item value

        Returns:
            True if stored successfully
        """
        self.items[key] = value
        print(f"📦 Storage: Stored {key}")
        return True

    @service("retrieve", scope=ServiceScope.PUBLIC)
    def retrieve_item(self, key: str) -> Any:
        """Retrieve an item.

        Args:
            key: Item key

        Returns:
            Item value or None if not found
        """
        value = self.items.get(key)
        print(f"🔍 Storage: Retrieved {key}")
        return value

    @service("list_keys", scope=ServiceScope.PUBLIC)
    def list_keys(self) -> list[str]:
        """List all keys.

        Returns:
            List of keys
        """
        keys = list(self.items.keys())
        print(f"📋 Storage: Listed {len(keys)} keys")
        return keys

    @service("delete", scope=ServiceScope.DEPENDENT)
    def delete_item(self, key: str) -> bool:
        """Delete an item (requires dependency).

        Args:
            key: Item key

        Returns:
            True if deleted successfully
        """
        if key in self.items:
            del self.items[key]
            print(f"🗑️ Storage: Deleted {key}")
            return True
        return False


# Task management plugin
class TaskPlugin(PepperpyPlugin):
    """A plugin that manages tasks and depends on storage."""

    __metadata__ = {
        "name": "tasks",
        "version": "1.0.0",
        "description": "Task management plugin",
        "author": "PepperPy Team",
        "provider_type": "tasks",
    }

    # Declare dependency on storage
    __dependencies__ = {
        "storage": DependencyType.REQUIRED,
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.active_tasks = 0

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register task counter as a resource
        self.register_resource(
            resource_key="active_tasks",
            resource=self.active_tasks,
            resource_type="metric",
            metadata={"description": "Number of active tasks"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    # Task management services

    @service("create_task", scope=ServiceScope.PUBLIC)
    async def create_task(
        self, task_id: str, description: str, assigned_to: str | None = ""
    ) -> bool:
        """Create a new task.

        Args:
            task_id: Unique task ID
            description: Task description
            assigned_to: Person assigned to the task

        Returns:
            True if task created successfully
        """
        # Create task data
        task = {
            "id": task_id,
            "description": description,
            "assigned_to": assigned_to,
            "status": "pending",
            "created_at": "now",
        }

        # Store task using storage plugin
        key = f"task:{task_id}"
        result = call_service("storage", "store", self.plugin_id, key, task)

        if result:
            self.active_tasks += 1

            # Publish event about task creation
            await self.publish(
                AppEventType.TASK_CREATED,
                data=task,
                context_data={"source": self.plugin_id},
            )

            print(f"📝 Tasks: Created task {task_id}")

        return result

    @service("complete_task", scope=ServiceScope.PUBLIC)
    async def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task ID

        Returns:
            True if task completed successfully
        """
        # Get the task
        key = f"task:{task_id}"
        task = call_service("storage", "retrieve", self.plugin_id, key)

        if not task:
            print(f"❌ Tasks: Task {task_id} not found")
            return False

        # Update the task
        task["status"] = "completed"
        task["completed_at"] = "now"

        # Store updated task
        result = call_service("storage", "store", self.plugin_id, key, task)

        if result:
            self.active_tasks -= 1

            # Publish event about task completion
            await self.publish(
                AppEventType.TASK_COMPLETED,
                data=task,
                context_data={"source": self.plugin_id},
            )

            print(f"✅ Tasks: Marked task {task_id} as completed")

        return result

    @service("list_tasks", scope=ServiceScope.PUBLIC)
    def list_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        """List all tasks, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of tasks
        """
        # Get all keys from storage
        keys = call_service("storage", "list_keys", self.plugin_id)

        # Filter task keys
        task_keys = [key for key in keys if key.startswith("task:")]

        # Get tasks
        tasks = []
        for key in task_keys:
            task = call_service("storage", "retrieve", self.plugin_id, key)
            if status is None or task["status"] == status:
                tasks.append(task)

        print(f"📋 Tasks: Listed {len(tasks)} tasks")
        return tasks

    # Event handlers

    @PepperpyPlugin.event_handler(AppEventType.TASK_COMPLETED, EventPriority.NORMAL)
    async def handle_task_completed(
        self, event_type: str, context: EventContext, data: dict[str, Any]
    ) -> None:
        """Handle task completed event."""
        task_id = data["id"]
        print(f"🔔 Tasks: Received notification about completed task {task_id}")


# File processing plugin
class FileProcessingPlugin(PepperpyPlugin):
    """A plugin that processes files and tasks."""

    __metadata__ = {
        "name": "file_processor",
        "version": "1.0.0",
        "description": "File processing plugin",
        "author": "PepperPy Team",
        "provider_type": "processing",
    }

    # Declare dependencies
    __dependencies__ = {
        "storage": DependencyType.REQUIRED,
        "tasks": DependencyType.OPTIONAL,
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.processors = {}
        self.processed_files = 0

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register processors dictionary as a resource
        self.register_resource(
            resource_key="processors",
            resource=self.processors,
            resource_type=ResourceType.MEMORY,
            metadata={"description": "File processors"},
        )

        # Register some file processors
        self.register_processor("text", self._process_text)
        self.register_processor("image", self._process_image)
        self.register_processor("document", self._process_document)

        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    def register_processor(self, file_type: str, processor_func: callable) -> None:
        """Register a file processor.

        Args:
            file_type: Type of file to process
            processor_func: Processor function
        """
        self.processors[file_type] = processor_func
        print(f"🔧 FileProcessor: Registered processor for {file_type} files")

    # File processing services

    @service("upload_file", scope=ServiceScope.PUBLIC)
    async def upload_file(self, file_id: str, file_type: str, content: Any) -> bool:
        """Upload a file for processing.

        Args:
            file_id: Unique file ID
            file_type: Type of file
            content: File content

        Returns:
            True if upload successful
        """
        # Store file data
        file_data = {
            "id": file_id,
            "type": file_type,
            "content": content,
            "status": "uploaded",
            "uploaded_at": "now",
        }

        # Store file using storage plugin
        key = f"file:{file_id}"
        result = call_service("storage", "store", self.plugin_id, key, file_data)

        if result:
            # Publish event about file upload
            await self.publish(
                AppEventType.FILE_UPLOADED,
                data=file_data,
                context_data={"source": self.plugin_id},
            )

            print(f"📤 FileProcessor: Uploaded file {file_id} ({file_type})")

            # Create a task for processing if task plugin is available
            try:
                if call_service("tasks", "list_tasks", self.plugin_id) is not None:
                    await call_service(
                        "tasks",
                        "create_task",
                        self.plugin_id,
                        f"process-file-{file_id}",
                        f"Process {file_type} file: {file_id}",
                        "system",
                    )
            except Exception as e:
                print(f"⚠️ FileProcessor: Could not create task - {e}")

        return result

    @service("process_file", scope=ServiceScope.PUBLIC)
    async def process_file(self, file_id: str) -> dict[str, Any]:
        """Process a file.

        Args:
            file_id: File ID

        Returns:
            Processing results
        """
        # Get the file
        key = f"file:{file_id}"
        file_data = call_service("storage", "retrieve", self.plugin_id, key)

        if not file_data:
            print(f"❌ FileProcessor: File {file_id} not found")
            return {"error": "File not found"}

        # Get the appropriate processor
        file_type = file_data["type"]
        processor = self.processors.get(file_type)

        if not processor:
            print(f"❌ FileProcessor: No processor for {file_type} files")
            return {"error": f"No processor for {file_type} files"}

        # Process the file
        print(f"⚙️ FileProcessor: Processing file {file_id} ({file_type})")
        processing_result = await processor(file_data)

        # Update file data
        file_data["status"] = "processed"
        file_data["processed_at"] = "now"
        file_data["processing_result"] = processing_result

        # Store updated file
        call_service("storage", "store", self.plugin_id, key, file_data)

        # Increment counter
        self.processed_files += 1

        # Publish event about file processing
        await self.publish(
            AppEventType.FILE_PROCESSED,
            data=file_data,
            context_data={"source": self.plugin_id},
        )

        # Complete the task if task plugin is available
        try:
            task_id = f"process-file-{file_id}"
            tasks = call_service("tasks", "list_tasks", self.plugin_id)

            for task in tasks:
                if task["id"] == task_id:
                    await call_service(
                        "tasks", "complete_task", self.plugin_id, task_id
                    )
                    break
        except Exception as e:
            print(f"⚠️ FileProcessor: Could not complete task - {e}")

        return processing_result

    # File processors

    async def _process_text(self, file_data: dict[str, Any]) -> dict[str, Any]:
        """Process a text file.

        Args:
            file_data: File data

        Returns:
            Processing results
        """
        # Simulate processing
        await asyncio.sleep(0.2)

        content = file_data["content"]
        return {
            "word_count": len(content.split()),
            "char_count": len(content),
            "summary": content[:50] + "..." if len(content) > 50 else content,
        }

    async def _process_image(self, file_data: dict[str, Any]) -> dict[str, Any]:
        """Process an image file.

        Args:
            file_data: File data

        Returns:
            Processing results
        """
        # Simulate processing
        await asyncio.sleep(0.5)

        return {"format": "jpeg", "dimensions": "800x600", "size": "250KB"}

    async def _process_document(self, file_data: dict[str, Any]) -> dict[str, Any]:
        """Process a document file.

        Args:
            file_data: File data

        Returns:
            Processing results
        """
        # Simulate processing
        await asyncio.sleep(0.7)

        return {
            "format": "pdf",
            "pages": 5,
            "extracted_text": "Sample document content...",
            "metadata": {"author": "Sample Author", "created": "2023-01-01"},
        }


# Notification plugin for analytics
class NotificationPlugin(PepperpyPlugin):
    """A plugin that listens for events and sends notifications."""

    __metadata__ = {
        "name": "notifications",
        "version": "1.0.0",
        "description": "Notification plugin",
        "author": "PepperPy Team",
        "provider_type": "notifications",
    }

    # No dependencies needed - uses events for communication

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.notifications = []

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register notifications list as a resource
        self.register_resource(
            resource_key="notifications",
            resource=self.notifications,
            resource_type=ResourceType.MEMORY,
            metadata={"description": "Sent notifications"},
        )

        # Set up event handlers for all app events with lowest priority
        for event_type in AppEventType:
            self.subscribe(
                event_type,
                self.handle_notification_event,
                EventPriority.LOWEST,
                # Receive notifications even if event was canceled
                call_if_canceled=True,
            )

        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    # Event handler for all events
    async def handle_notification_event(
        self, event_type: str, context: EventContext, data: dict[str, Any]
    ) -> None:
        """Handle any application event by creating a notification.

        Args:
            event_type: Event type
            context: Event context
            data: Event data
        """
        # Create notification based on event type
        notification = {
            "event_type": event_type,
            "timestamp": "now",
            "source": context.source,
            "message": self._create_message(event_type, data),
            "data": data,
        }

        # Add to notifications
        self.notifications.append(notification)

        # Print notification
        print(f"🔔 Notification: {notification['message']}")

    def _create_message(self, event_type: str, data: dict[str, Any]) -> str:
        """Create a user-friendly message based on the event type.

        Args:
            event_type: Event type
            data: Event data

        Returns:
            Notification message
        """
        if event_type == AppEventType.TASK_CREATED.value:
            return f"New task created: {data['id']} - {data['description']}"
        elif event_type == AppEventType.TASK_COMPLETED.value:
            return f"Task completed: {data['id']} - {data['description']}"
        elif event_type == AppEventType.FILE_UPLOADED.value:
            return f"New file uploaded: {data['id']} ({data['type']})"
        elif event_type == AppEventType.FILE_PROCESSED.value:
            return f"File processed: {data['id']} ({data['type']})"
        else:
            return f"Event received: {event_type}"

    # Notification service

    @service("get_notifications", scope=ServiceScope.PUBLIC)
    def get_notifications(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get recent notifications.

        Args:
            limit: Maximum number of notifications to return

        Returns:
            List of notifications
        """
        notifications = list(self.notifications)

        # Sort by most recent first (assuming we had real timestamps)
        notifications.reverse()

        # Apply limit if specified
        if limit is not None:
            notifications = notifications[:limit]

        return notifications


async def main():
    """Run the example."""
    print("🚀 Starting complete plugin system example")

    # Create plugins
    storage = StoragePlugin()
    tasks = TaskPlugin()
    file_processor = FileProcessingPlugin()
    notifications = NotificationPlugin()

    # Initialize plugins in dependency order
    print("\n📦 Initializing plugins:")
    storage.initialize()
    tasks.initialize()
    file_processor.initialize()
    notifications.initialize()

    # Create some tasks
    print("\n📝 Creating tasks:")
    await tasks.create_task("task1", "Write documentation", "alice")
    await tasks.create_task("task2", "Fix bugs", "bob")
    await tasks.create_task("task3", "Deploy application", "charlie")

    # Upload some files
    print("\n📤 Uploading files:")
    await file_processor.upload_file(
        "file1", "text", "This is a sample text file with some content for processing."
    )
    await file_processor.upload_file(
        "file2", "image", "binary_image_content_placeholder"
    )
    await file_processor.upload_file(
        "file3", "document", "binary_document_content_placeholder"
    )

    # Process files
    print("\n⚙️ Processing files:")
    await file_processor.process_file("file1")
    await file_processor.process_file("file2")
    await file_processor.process_file("file3")

    # Complete some tasks
    print("\n✅ Completing tasks:")
    await tasks.complete_task("task1")
    await tasks.complete_task("task3")

    # List tasks
    print("\n📋 Active tasks:")
    active_tasks = tasks.list_tasks(status="pending")
    for task in active_tasks:
        print(
            f"  - {task['id']}: {task['description']} (Assigned to: {task['assigned_to']})"
        )

    # Get notifications
    print("\n🔔 Recent notifications (last 5):")
    recent_notifications = notifications.get_notifications(limit=5)
    for notification in recent_notifications:
        print(f"  - {notification['message']}")

    # Clean up plugins in reverse dependency order
    print("\n🧹 Cleaning up...")
    await notifications.async_cleanup()
    await file_processor.async_cleanup()
    await tasks.async_cleanup()
    await storage.async_cleanup()

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
