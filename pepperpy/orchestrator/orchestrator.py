"""Orchestrator implementation.

This module provides functionality for orchestrating AI components,
including task scheduling, resource management, and error handling.
"""

from abc import ABC, abstractmethod
import asyncio
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.events import Event, EventBus
from pepperpy.monitoring import Monitor
from pepperpy.runtime import Environment, Executor
from .task import Task, TaskError, TaskStatus

T = TypeVar("T")


class OrchestratorError(PepperpyError):
    """Orchestrator error."""
    pass


class Orchestrator(Lifecycle):
    """Orchestrator implementation."""
    
    def __init__(
        self,
        name: str,
        environment: Environment,
        executor: Executor,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize orchestrator.
        
        Args:
            name: Orchestrator name
            environment: Runtime environment
            executor: Task executor
            event_bus: Optional event bus
            monitor: Optional monitor
            config: Optional configuration
        """
        super().__init__()
        self.name = name
        self._environment = environment
        self._executor = executor
        self._event_bus = event_bus
        self._monitor = monitor
        self._config = config or {}
        self._tasks: Dict[str, Task[Any]] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        
    def add_task(self, task: Task[T]) -> None:
        """Add task.
        
        Args:
            task: Task to add
            
        Raises:
            OrchestratorError: If task already exists
        """
        if task.id in self._tasks:
            raise OrchestratorError(f"Task already exists: {task.id}")
            
        self._tasks[task.id] = task
        
    def remove_task(self, task_id: str) -> None:
        """Remove task.
        
        Args:
            task_id: Task ID
            
        Raises:
            OrchestratorError: If task not found
        """
        if task_id not in self._tasks:
            raise OrchestratorError(f"Task not found: {task_id}")
            
        task = self._tasks[task_id]
        if task.status == TaskStatus.RUNNING:
            raise OrchestratorError("Cannot remove running task")
            
        del self._tasks[task_id]
        
        if task_id in self._dependencies:
            del self._dependencies[task_id]
            
        for deps in self._dependencies.values():
            deps.discard(task_id)
            
    def add_dependency(
        self,
        task_id: str,
        dependency_id: str,
    ) -> None:
        """Add task dependency.
        
        Args:
            task_id: Task ID
            dependency_id: Dependency task ID
            
        Raises:
            OrchestratorError: If tasks not found or cycle detected
        """
        if task_id not in self._tasks:
            raise OrchestratorError(f"Task not found: {task_id}")
            
        if dependency_id not in self._tasks:
            raise OrchestratorError(f"Dependency not found: {dependency_id}")
            
        if task_id == dependency_id:
            raise OrchestratorError("Self dependency not allowed")
            
        if task_id not in self._dependencies:
            self._dependencies[task_id] = set()
            
        self._dependencies[task_id].add(dependency_id)
        
        # Check for cycles
        visited = set()
        stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            stack.add(node)
            
            for dep in self._dependencies.get(node, set()):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in stack:
                    return True
                    
            stack.remove(node)
            return False
            
        if has_cycle(task_id):
            self._dependencies[task_id].remove(dependency_id)
            raise OrchestratorError("Dependency cycle detected")
            
    async def execute(self, task_id: str) -> T:
        """Execute task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result
            
        Raises:
            OrchestratorError: If execution fails
        """
        if task_id not in self._tasks:
            raise OrchestratorError(f"Task not found: {task_id}")
            
        task = self._tasks[task_id]
        if task.status == TaskStatus.RUNNING:
            raise OrchestratorError("Task already running")
            
        # Wait for dependencies
        deps = self._dependencies.get(task_id, set())
        for dep_id in deps:
            dep = self._tasks[dep_id]
            if dep.status != TaskStatus.COMPLETED:
                raise OrchestratorError(
                    f"Dependency not completed: {dep_id}"
                )
                
        # Execute task
        try:
            task.status = TaskStatus.RUNNING
            
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="task_started",
                        source=self.name,
                        timestamp=task.start_time,
                        data={"task_id": task_id},
                    )
                )
                
            result = await self._executor.execute(task)
            task.status = TaskStatus.COMPLETED
            task.result = result
            
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="task_completed",
                        source=self.name,
                        timestamp=task.end_time,
                        data={
                            "task_id": task_id,
                            "result": result,
                        },
                    )
                )
                
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = e
            
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="task_failed",
                        source=self.name,
                        timestamp=task.end_time,
                        data={
                            "task_id": task_id,
                            "error": str(e),
                        },
                    )
                )
                
            raise OrchestratorError(f"Task execution failed: {e}")
            
    async def execute_all(self) -> None:
        """Execute all tasks.
        
        Raises:
            OrchestratorError: If execution fails
        """
        async with self._lock:
            # Reset task states
            for task in self._tasks.values():
                task.status = TaskStatus.PENDING
                task.result = None
                task.error = None
                
            # Execute tasks in dependency order
            executed = set()
            tasks = []
            
            async def exec_task(task_id: str) -> None:
                # Wait for dependencies
                deps = self._dependencies.get(task_id, set())
                for dep_id in deps:
                    if dep_id not in executed:
                        await asyncio.Event().wait()
                        
                try:
                    await self.execute(task_id)
                    executed.add(task_id)
                except Exception as e:
                    raise OrchestratorError(
                        f"Task execution failed: {task_id} - {e}"
                    )
                    
            for task_id in self._tasks:
                task = asyncio.create_task(exec_task(task_id))
                tasks.append(task)
                
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                raise OrchestratorError(f"Orchestrator execution failed: {e}")
                
    async def _initialize(self) -> None:
        """Initialize orchestrator."""
        await self._environment.initialize()
        await self._executor.initialize()
        
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up orchestrator."""
        if self._monitor:
            await self._monitor.cleanup()
            
        if self._event_bus:
            await self._event_bus.cleanup()
            
        await self._executor.cleanup()
        await self._environment.cleanup()
        
    def validate(self) -> None:
        """Validate orchestrator state."""
        super().validate()
        
        if not self.name:
            raise OrchestratorError("Empty orchestrator name")
            
        if not self._environment:
            raise OrchestratorError("Missing environment")
            
        if not self._executor:
            raise OrchestratorError("Missing executor")
            
        self._environment.validate()
        self._executor.validate()
        
        if self._event_bus:
            self._event_bus.validate()
            
        if self._monitor:
            self._monitor.validate() 