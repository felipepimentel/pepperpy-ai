"""Core type definitions for the PepperPy framework.

This module defines the fundamental types used throughout the PepperPy framework.
These types provide a common vocabulary for working with data in the framework.
"""

from typing import Any, Dict, List, Union, Optional, TypeVar, Generic
from pathlib import Path
import os

# JSON-related types
JSON = Dict[str, Any]
JSONValue = Union[str, int, float, bool, None, List[Any], Dict[str, Any]]

# Path-related types
PathType = Union[str, Path, os.PathLike]

# Generic type variables
T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')

# Result types
class Result(Generic[T]):
    """A container for the result of an operation that might fail."""
    
    def __init__(self, value: Optional[T] = None, error: Optional[Exception] = None):
        """Initialize the result with a value or an error."""
        self._value = value
        self._error = error
    
    @property
    def value(self) -> T:
        """Return the value if the operation succeeded."""
        if self._error:
            raise ValueError(f"Cannot access value of failed result: {self._error}")
        return self._value
    
    @property
    def error(self) -> Optional[Exception]:
        """Return the error if the operation failed."""
        return self._error
    
    @property
    def is_success(self) -> bool:
        """Return whether the operation succeeded."""
        return self._error is None
    
    @property
    def is_failure(self) -> bool:
        """Return whether the operation failed."""
        return self._error is not None
    
    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        """Create a successful result with the provided value."""
        return cls(value=value)
    
    @classmethod
    def failure(cls, error: Exception) -> 'Result[T]':
        """Create a failed result with the provided error."""
        return cls(error=error)
