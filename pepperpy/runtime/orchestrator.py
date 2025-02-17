"""@file: orchestrator.py
@purpose: Runtime task orchestration and workflow management
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON
from pepperpy.runtime.context import get_current_context
from pepperpy.runtime.lifecycle import get_lifecycle_manager

logger = get_logger(__name__)


class TaskState(str, Enum):
    """Possible states of a runtime task."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Runtime task for execution."""

    name: str
    handler: Callable[..., Any]
    id: UUID = field(default_factory=uuid4)
    state: TaskState = field(default=TaskState.CREATED)
    priority: int = field(default=0)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[UUID] = field(default_factory=set)

    def to_json(self) -> JSON:
        """Convert task to JSON format."""
        return {
            "id": str(self.id),
            "name": self.name,
            "state": self.state.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "result": str(self.result) if self.result else None,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata,
            "dependencies": [str(dep) for dep in self.dependencies],
        }


@dataclass
class OrchestratorConfig:
    """Configuration for task orchestration."""

    max_concurrent_tasks: int = 10
    max_queue_size: int = 1000
    task_timeout: float = 3600.0  # Default timeout of 1 hour
    cleanup_interval: float = 300.0  # Cleanup every 5 minutes

    def validate(self) -> None:
        """Validate orchestrator configuration."""
        if self.max_concurrent_tasks < 1:
            raise ConfigurationError("Max concurrent tasks must be positive")
        if self.max_queue_size < 1:
            raise ConfigurationError("Max queue size must be positive")
        if self.task_timeout <= 0:
            raise ConfigurationError("Task timeout must be positive")
        if self.cleanup_interval <= 0:
            raise ConfigurationError("Cleanup interval must be positive")


class TaskManager:
    """Manager for runtime tasks."""

    def __init__(self) -> None:
        """Initialize task manager."""
        self._tasks: Dict[UUID, Task] = {}
        self._lock = threading.Lock()

    def create(
        self,
        name: str,
        handler: Callable[..., Any],
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Set[UUID]] = None,
    ) -> Task:
        """Create a new task.

        Args:
            name: Task name
            handler: Task handler function
            priority: Task priority (higher is more important)
            metadata: Optional task metadata
            dependencies: Optional task dependencies

        Returns:
            Created task instance

        """
        task = Task(
            name=name,
            handler=handler,
            priority=priority,
            metadata=metadata or {},
            dependencies=dependencies or set(),
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get(self, task_id: UUID) -> Optional[Task]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise

        """
        return self._tasks.get(task_id)

    def update_state(self, task_id: UUID, state: TaskState) -> None:
        """Update task state.

        Args:
            task_id: Task ID
            state: New state

        Raises:
            StateError: If task not found

        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise StateError(f"Task not found: {task_id}")
            task.state = state
            if state == TaskState.RUNNING:
                task.started_at = datetime.utcnow()
            elif state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}:
                task.completed_at = datetime.utcnow()

    def cleanup(self) -> None:
        """Clean up completed tasks."""
        with self._lock:
            for task_id in list(self._tasks.keys()):
                task = self._tasks[task_id]
                if task.state in {
                    TaskState.COMPLETED,
                    TaskState.FAILED,
                    TaskState.CANCELLED,
                }:
                    del self._tasks[task_id]


class Orchestrator:
    """Runtime task orchestrator."""

    def __init__(self, config: Optional[OrchestratorConfig] = None) -> None:
        """Initialize orchestrator.

        Args:
            config: Optional orchestrator configuration

        """
        self.config = config or OrchestratorConfig()
        self.config.validate()

        self._task_manager = TaskManager()
        self._queue: List[Task] = []
        self._running: Set[UUID] = set()
        self._lock = threading.Lock()
        self._event = asyncio.Event()
        self._lifecycle = get_lifecycle_manager().create(
            context=get_current_context(),
            metadata={"component": "orchestrator"},
        )

    async def submit(
        self,
        name: str,
        handler: Callable[..., Any],
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Set[UUID]] = None,
    ) -> Task:
        """Submit a task for execution.

        Args:
            name: Task name
            handler: Task handler function
            priority: Task priority
            metadata: Optional task metadata
            dependencies: Optional task dependencies

        Returns:
            Submitted task instance

        Raises:
            ConfigurationError: If queue is full

        """
        with self._lock:
            if len(self._queue) >= self.config.max_queue_size:
                raise ConfigurationError("Task queue is full")

            task = self._task_manager.create(
                name=name,
                handler=handler,
                priority=priority,
                metadata=metadata,
                dependencies=dependencies,
            )
            self._queue.append(task)
            self._queue.sort(key=lambda t: t.priority, reverse=True)
            self._task_manager.update_state(task.id, TaskState.QUEUED)
            self._event.set()

        return task

    async def cancel(self, task_id: UUID) -> None:
        """Cancel a task.

        Args:
            task_id: Task ID to cancel

        Raises:
            StateError: If task not found or already completed

        """
        with self._lock:
            task = self._task_manager.get(task_id)
            if not task:
                raise StateError(f"Task not found: {task_id}")
            if task.state in {
                TaskState.COMPLETED,
                TaskState.FAILED,
                TaskState.CANCELLED,
            }:
                raise StateError(f"Task already completed: {task_id}")

            if task.state == TaskState.QUEUED:
                self._queue.remove(task)
            elif task.state == TaskState.RUNNING:
                self._running.remove(task.id)

            self._task_manager.update_state(task.id, TaskState.CANCELLED)

    async def run(self) -> None:
        """Run the orchestrator."""
        while True:
            await self._event.wait()
            self._event.clear()

            with self._lock:
                # Clean up completed tasks
                self._task_manager.cleanup()

                # Process queue
                while (
                    self._queue
                    and len(self._running) < self.config.max_concurrent_tasks
                ):
                    task = self._queue[0]
                    if not self._can_run(task):
                        break

                    self._queue.pop(0)
                    self._running.add(task.id)
                    self._task_manager.update_state(task.id, TaskState.RUNNING)
                    asyncio.create_task(self._execute_task(task))

    def _can_run(self, task: Task) -> bool:
        """Check if a task can run.

        Args:
            task: Task to check

        Returns:
            Whether the task can run

        """
        for dep_id in task.dependencies:
            dep_task = self._task_manager.get(dep_id)
            if not dep_task or dep_task.state != TaskState.COMPLETED:
                return False
        return True

    async def _execute_task(self, task: Task) -> None:
        """Execute a task.

        Args:
            task: Task to execute

        """
        try:
            task.result = await asyncio.wait_for(
                task.handler(),
                timeout=self.config.task_timeout,
            )
            self._task_manager.update_state(task.id, TaskState.COMPLETED)
        except Exception as e:
            task.error = e
            self._task_manager.update_state(task.id, TaskState.FAILED)
            logger.error(f"Task failed: {e}", extra={"task_id": str(task.id)})
        finally:
            with self._lock:
                self._running.remove(task.id)
                self._event.set()


# Global orchestrator instance
_orchestrator = Orchestrator()


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance.

    Returns:
        Global orchestrator instance

    """
    return _orchestrator
