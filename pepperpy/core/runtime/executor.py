"""Runtime executor for Pepperpy.

This module provides functionality for executing tasks and managing their
lifecycle in the runtime environment.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ExecutorError(PepperpyError):
    """Executor error."""
    pass


T = TypeVar("T")


class Task(Protocol[T]):
    """Task protocol."""
    
    async def execute(self) -> T:
        """Execute task.
        
        Returns:
            Task result
            
        Raises:
            ExecutorError: If task execution fails
        """
        raise NotImplementedError


class Executor(Lifecycle):
    """Runtime task executor."""
    
    def __init__(
        self,
        name: str,
        max_concurrent: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize executor.
        
        Args:
            name: Executor name
            max_concurrent: Optional maximum concurrent tasks
            config: Optional executor configuration
        """
        super().__init__()
        self.name = name
        self._max_concurrent = max_concurrent
        self._config = config or {}
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._tasks: List[asyncio.Task[Any]] = []
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get executor configuration."""
        return self._config
        
    async def initialize(self) -> None:
        """Initialize executor."""
        if self._max_concurrent:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
            
    async def cleanup(self) -> None:
        """Clean up executor."""
        # Cancel running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        self._tasks.clear()
        
    async def execute(self, task: Task[T]) -> T:
        """Execute task.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
            
        Raises:
            ExecutorError: If task execution fails
        """
        try:
            if self._semaphore:
                async with self._semaphore:
                    return await task.execute()
            else:
                return await task.execute()
                
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise ExecutorError(str(e))
            
    async def execute_batch(
        self,
        tasks: List[Task[T]],
        max_concurrent: Optional[int] = None,
    ) -> List[T]:
        """Execute batch of tasks.
        
        Args:
            tasks: Tasks to execute
            max_concurrent: Optional maximum concurrent tasks
            
        Returns:
            List of task results
            
        Raises:
            ExecutorError: If task execution fails
        """
        if not tasks:
            return []
            
        try:
            semaphore = None
            if max_concurrent:
                semaphore = asyncio.Semaphore(max_concurrent)
                
            async def _execute_with_semaphore(task: Task[T]) -> T:
                if semaphore:
                    async with semaphore:
                        return await task.execute()
                else:
                    return await task.execute()
                    
            # Create tasks
            coros = [_execute_with_semaphore(task) for task in tasks]
            tasks = [asyncio.create_task(coro) for coro in coros]
            self._tasks.extend(tasks)
            
            # Wait for tasks to complete
            results = await asyncio.gather(*tasks)
            
            # Remove completed tasks
            for task in tasks:
                self._tasks.remove(task)
                
            return results
            
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise ExecutorError(str(e))
            
    def validate(self) -> None:
        """Validate executor state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Executor name cannot be empty") 