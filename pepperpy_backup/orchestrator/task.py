"""Task implementation.

This module provides functionality for defining and managing tasks,
including task status, dependencies, and error handling.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Generic, Optional, TypeVar

from pepperpy.common.errors import PepperpyError

T = TypeVar("T")


class TaskError(PepperpyError):
    """Task error."""
    pass


class TaskStatus(Enum):
    """Task status."""
    
    PENDING = auto()
    """Task is pending execution."""
    
    RUNNING = auto()
    """Task is running."""
    
    COMPLETED = auto()
    """Task completed successfully."""
    
    FAILED = auto()
    """Task failed."""


class Task(Generic[T], ABC):
    """Task interface."""
    
    def __init__(
        self,
        id: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize task.
        
        Args:
            id: Task ID
            name: Task name
            config: Optional configuration
        """
        self.id = id
        self.name = name
        self._config = config or {}
        self._status = TaskStatus.PENDING
        self._result: Optional[T] = None
        self._error: Optional[Exception] = None
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        
    @property
    def status(self) -> TaskStatus:
        """Get task status.
        
        Returns:
            Task status
        """
        return self._status
        
    @status.setter
    def status(self, value: TaskStatus) -> None:
        """Set task status.
        
        Args:
            value: Task status
        """
        if value == TaskStatus.RUNNING:
            self._start_time = datetime.now()
        elif value in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            self._end_time = datetime.now()
            
        self._status = value
        
    @property
    def result(self) -> Optional[T]:
        """Get task result.
        
        Returns:
            Task result if any
        """
        return self._result
        
    @result.setter
    def result(self, value: Optional[T]) -> None:
        """Set task result.
        
        Args:
            value: Task result
        """
        self._result = value
        
    @property
    def error(self) -> Optional[Exception]:
        """Get task error.
        
        Returns:
            Task error if any
        """
        return self._error
        
    @error.setter
    def error(self, value: Optional[Exception]) -> None:
        """Set task error.
        
        Args:
            value: Task error
        """
        self._error = value
        
    @property
    def start_time(self) -> Optional[datetime]:
        """Get task start time.
        
        Returns:
            Task start time if any
        """
        return self._start_time
        
    @property
    def end_time(self) -> Optional[datetime]:
        """Get task end time.
        
        Returns:
            Task end time if any
        """
        return self._end_time
        
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds.
        
        Returns:
            Task duration if completed
        """
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time).total_seconds()
        return None
        
    @abstractmethod
    async def execute(self) -> T:
        """Execute task.
        
        Returns:
            Task result
            
        Raises:
            TaskError: If execution fails
        """
        pass
        
    def validate(self) -> None:
        """Validate task state.
        
        Raises:
            TaskError: If validation fails
        """
        if not self.id:
            raise TaskError("Empty task ID")
            
        if not self.name:
            raise TaskError("Empty task name")
            
        if self._status == TaskStatus.COMPLETED and self._result is None:
            raise TaskError("Missing task result")
            
        if self._status == TaskStatus.FAILED and self._error is None:
            raise TaskError("Missing task error") 