"""Common data types for Pepperpy."""

from typing import Any, Protocol, TypeVar, runtime_checkable

# Type variables for data types
T = TypeVar("T")

@runtime_checkable
class Mergeable(Protocol[T]):
    """Protocol for objects that can be merged."""
    
    def merge(self, other: T) -> T:
        """Merge another object into this one."""
        ...

@runtime_checkable
class Versionable(Protocol):
    """Protocol for objects that can be versioned."""
    
    @property
    def version(self) -> str:
        """Return object version."""
        ...
        
    def is_compatible(self, other: Any) -> bool:
        """Check version compatibility."""
        ... 