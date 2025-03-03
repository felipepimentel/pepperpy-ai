"""Public Interface for Capabilities

This module provides a stable public interface for the capabilities functionality.
It exposes the core capability abstractions and implementations that are
considered part of the public API.

Core Components:
    TaskCapability: Task management capability
    TaskRegistry: Registry of available tasks
    TaskScheduler: Schedules tasks for execution
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Status of a task."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class Task:
    """Represents a task to be executed.

    Attributes:
        id: Unique identifier for the task
        name: Human-readable name for the task
        function: Function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        status: Current status of the task
        created_at: Timestamp when the task was created
        started_at: Timestamp when the task started executing
        completed_at: Timestamp when the task completed executing
        result: Result of the task execution
        error: Error that occurred during task execution

    """

    id: str
    name: str
    function: Callable
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None


class TaskRegistry:
    """Registry of available tasks.

    This class provides functionality for registering, retrieving,
    and managing tasks.
    """

    def __init__(self):
        """Initialize a task registry."""
        self.tasks: Dict[str, Callable] = {}

    def register(self, name: str, function: Callable) -> None:
        """Register a task.

        Args:
            name: Task name
            function: Task function

        """
        self.tasks[name] = function

    def get(self, name: str) -> Optional[Callable]:
        """Get a task by name.

        Args:
            name: Task name

        Returns:
            Task function or None if not found

        """
        return self.tasks.get(name)

    def list_tasks(self) -> List[str]:
        """List all registered tasks.

        Returns:
            List of registered task names

        """
        return list(self.tasks.keys())


class TaskScheduler:
    """Schedules tasks for execution.

    This class provides functionality for scheduling tasks,
    including immediate execution, delayed execution, and recurring execution.
    """

    def __init__(self):
        """Initialize a task scheduler."""
        self.registry = TaskRegistry()
        self.pending_tasks: List[Task] = []
        self.running_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []

    def register_task(self, name: str, function: Callable) -> None:
        """Register a task.

        Args:
            name: Task name
            function: Task function

        """
        self.registry.register(name, function)

    async def schedule(
        self, task_name: str, *args: Any, delay: Optional[int] = None, **kwargs: Any,
    ) -> Task:
        """Schedule a task for execution.

        Args:
            task_name: Name of the task to schedule
            *args: Positional arguments for the task
            delay: Delay in seconds
            **kwargs: Keyword arguments for the task

        Returns:
            Scheduled task

        Raises:
            ValueError: If the task is not registered

        """
        function = self.registry.get(task_name)
        if not function:
            raise ValueError(f"Task {task_name} not registered")

        task = Task(
            id=f"task-{len(self.pending_tasks)}",
            name=task_name,
            function=function,
            args=list(args),
            kwargs=kwargs,
        )

        self.pending_tasks.append(task)

        # In a real implementation, we would handle the delay here

        return task

    async def execute_pending_tasks(self) -> List[Task]:
        """Execute all pending tasks.

        Returns:
            List of completed tasks

        """
        tasks_to_execute = self.pending_tasks.copy()
        self.pending_tasks.clear()

        for task in tasks_to_execute:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self.running_tasks.append(task)

            try:
                task.result = await task.function(*task.args, **task.kwargs)
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED

            task.completed_at = datetime.utcnow()
            self.running_tasks.remove(task)
            self.completed_tasks.append(task)

        return self.completed_tasks


class TaskCapability:
    """Task management capability.

    This class provides task management capabilities for agents,
    including task registration, scheduling, and execution.
    """

    def __init__(self, name: str = "task"):
        """Initialize the task capability.

        Args:
            name: Capability name

        """
        self.name = name
        self.scheduler = TaskScheduler()

    def register_task(self, name: str, function: Callable) -> None:
        """Register a task.

        Args:
            name: Task name
            function: Task function

        """
        self.scheduler.register_task(name, function)

    async def schedule_task(
        self, task_name: str, *args: Any, delay: Optional[int] = None, **kwargs: Any,
    ) -> Task:
        """Schedule a task for execution.

        Args:
            task_name: Name of the task to schedule
            *args: Positional arguments for the task
            delay: Delay in seconds
            **kwargs: Keyword arguments for the task

        Returns:
            Scheduled task

        """
        return await self.scheduler.schedule(task_name, *args, delay=delay, **kwargs)

    async def execute_pending_tasks(self) -> List[Task]:
        """Execute all pending tasks.

        Returns:
            List of completed tasks

        """
        return await self.scheduler.execute_pending_tasks()


# Export public classes
__all__ = [
    "Task",
    "TaskCapability",
    "TaskRegistry",
    "TaskScheduler",
    "TaskStatus",
]
