"""Task implementation.

This module provides functionality for defining and managing tasks,
including task status, dependencies, and error handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar

from pepperpy.common.errors import PepperpyError

T = TypeVar("T")


class TaskError(PepperpyError):
    """Task error."""
    pass


class TaskStatus(Enum):
    """Task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task(Generic[T], ABC):
    """Task class."""
    
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[T] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _config: Dict[str, Any] = field(default_factory=dict)
    _start_time: datetime = field(default_factory=datetime.now, init=False)
    _end_time: datetime = field(default_factory=datetime.now, init=False)
    
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
        """Validate task state."""
        if not self.id:
            raise TaskError("Empty task ID")
            
        if not self.name:
            raise TaskError("Empty task name")
            
        if self.status == TaskStatus.COMPLETED and self.result is None:
            raise TaskError("Missing task result")
            
        if self.status == TaskStatus.FAILED and self.error is None:
            raise TaskError("Missing task error")
    
    @property
    def start_time(self) -> datetime:
        """Return task start time."""
        return self._start_time
        
    @start_time.setter
    def start_time(self, value: datetime) -> None:
        """Set task start time."""
        self._start_time = value
        
    @property
    def end_time(self) -> datetime:
        """Return task end time."""
        return self._end_time
        
    @end_time.setter
    def end_time(self, value: datetime) -> None:
        """Set task end time."""
        self._end_time = value
        
    @property
    def duration(self) -> float:
        """Return task duration in seconds."""
        return (self.end_time - self.start_time).total_seconds() 