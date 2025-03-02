"""
Task capability interface.

This module provides the public interface for task capabilities.
"""

from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from pepperpy.capabilities import CapabilityType
from pepperpy.capabilities.base import BaseCapability, CapabilityConfig


class TaskCapability(BaseCapability):
    """Base class for task capabilities.

    This class defines the interface that all task capabilities must implement.
    """

    def __init__(self, config: Optional[CapabilityConfig] = None):
        """Initialize task capability.

        Args:
            config: Optional configuration for the capability
        """
        super().__init__(CapabilityType.TASK, config)

    async def execute(self, task_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a task.

        Args:
            task_id: Task identifier
            params: Optional parameters for the task

        Returns:
            Task result

        Raises:
            NotImplementedError: If not implemented by subclass
            TaskNotFoundError: If task doesn't exist
            TaskExecutionError: If task execution fails
        """
        raise NotImplementedError("Task capability must implement execute method")

    async def cancel(self, task_id: str) -> bool:
        """Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled, False otherwise

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Task capability must implement cancel method")

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Task status information

        Raises:
            NotImplementedError: If not implemented by subclass
            TaskNotFoundError: If task doesn't exist
        """
        raise NotImplementedError("Task capability must implement get_status method")


class TaskScheduler(TaskCapability):
    """Task capability for scheduling and managing tasks.

    This class provides methods for scheduling, executing, and
    monitoring tasks.
    """

    async def schedule(
        self, task_id: str, params: Optional[Dict[str, Any]] = None, delay: Optional[int] = None
    ) -> str:
        """Schedule a task for execution.

        Args:
            task_id: Task identifier
            params: Optional parameters for the task
            delay: Optional delay in seconds

        Returns:
            Scheduled task identifier
        """
        pass

    async def schedule_recurring(
        self, task_id: str, params: Optional[Dict[str, Any]] = None, interval: int
    ) -> str:
        """Schedule a recurring task.

        Args:
            task_id: Task identifier
            params: Optional parameters for the task
            interval: Interval in seconds

        Returns:
            Scheduled task identifier
        """
        pass

    async def list_scheduled(self) -> List[Dict[str, Any]]:
        """List scheduled tasks.

        Returns:
            List of scheduled task information
        """
        pass


class TaskRegistry(TaskCapability):
    """Registry for task definitions.

    This class provides methods for registering and managing
    task definitions.
    """

    async def register(
        self, task_id: str, handler: Callable[..., Awaitable[Any]], metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a task handler.

        Args:
            task_id: Task identifier
            handler: Task handler function
            metadata: Optional task metadata
        """
        pass

    async def unregister(self, task_id: str) -> bool:
        """Unregister a task handler.

        Args:
            task_id: Task identifier

        Returns:
            True if task was unregistered, False if task doesn't exist
        """
        pass

    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List registered tasks.

        Returns:
            List of task information
        """
        pass


# Export public classes
__all__ = [
    "TaskCapability",
    "TaskScheduler",
    "TaskRegistry",
] 