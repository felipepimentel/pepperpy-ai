"""Core types and protocols for Pepperpy."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, runtime_checkable

# Type variables for generic types
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Base class for all Pepperpy objects
class PepperpyObject(ABC):
    """Base class for all Pepperpy objects."""
    
    @abstractmethod
    def __repr__(self) -> str:
        """Return string representation of the object."""
        ...

# Protocol for objects that can be initialized from a dictionary
@runtime_checkable
class DictInitializable(Protocol):
    """Protocol for objects that can be initialized from a dictionary."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Initialize object from dictionary."""
        ...
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        ...

# Protocol for objects that can be cloned
@runtime_checkable
class Cloneable(Protocol[T]):
    """Protocol for objects that can be cloned."""
    
    def clone(self) -> T:
        """Create a deep copy of the object."""
        ...

# Protocol for objects that can be validated
@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> None:
        """Validate object state."""
        ...

# Protocol for objects that can be serialized
@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized."""
    
    def serialize(self) -> bytes:
        """Serialize object to bytes."""
        ...
        
    @classmethod
    def deserialize(cls, data: bytes) -> Any:
        """Deserialize object from bytes."""
        ...

# Protocol for objects that can be compared for equality
@runtime_checkable
class Equatable(Protocol):
    """Protocol for objects that can be compared for equality."""
    
    def __eq__(self, other: Any) -> bool:
        """Compare objects for equality."""
        ...
        
    def __hash__(self) -> int:
        """Return hash value for object."""
        ...

# Protocol for objects that can be compared for ordering
@runtime_checkable
class Comparable(Equatable, Protocol):
    """Protocol for objects that can be compared for ordering."""
    
    def __lt__(self, other: Any) -> bool:
        """Compare objects for less than."""
        ...

# Protocol for objects that can be converted to strings
@runtime_checkable
class Stringable(Protocol):
    """Protocol for objects that can be converted to strings."""
    
    def __str__(self) -> str:
        """Convert object to string."""
        ...

# Protocol for objects that support context management
@runtime_checkable
class ContextManageable(Protocol):
    """Protocol for objects that support context management."""
    
    async def __aenter__(self) -> Any:
        """Enter async context."""
        ...
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        ...

# Protocol for objects that can be disposed
@runtime_checkable
class Disposable(Protocol):
    """Protocol for objects that can be disposed."""
    
    async def dispose(self) -> None:
        """Dispose of object resources."""
        ... 