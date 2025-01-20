"""Type utilities for Pepperpy."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, runtime_checkable

# Type variables
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Common type aliases
JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
JSONDict = Dict[str, JSON]
JSONList = List[JSON]

PathLike = Union[str, "Path"]
DictStrAny = Dict[str, Any]
DictStrStr = Dict[str, str]
ListStr = List[str]

# Protocol for objects that can be converted to/from dictionaries
@runtime_checkable
class DictConvertible(Protocol):
    """Protocol for objects that can be converted to/from dictionaries."""
    
    def to_dict(self) -> DictStrAny:
        """Convert object to dictionary."""
        ...
        
    @classmethod
    def from_dict(cls, data: DictStrAny) -> Any:
        """Create object from dictionary."""
        ...

# Protocol for objects that can be serialized to/from JSON
@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for objects that can be serialized to/from JSON."""
    
    def to_json(self) -> str:
        """Convert object to JSON string."""
        ...
        
    @classmethod
    def from_json(cls, json_str: str) -> Any:
        """Create object from JSON string."""
        ...

# Protocol for objects that can be validated
@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> None:
        """Validate object state."""
        ...

# Protocol for objects that can be cloned
@runtime_checkable
class Cloneable(Protocol[T]):
    """Protocol for objects that can be cloned."""
    
    def clone(self) -> T:
        """Create a deep copy of the object."""
        ...

# Protocol for objects that can be merged
@runtime_checkable
class Mergeable(Protocol[T]):
    """Protocol for objects that can be merged."""
    
    def merge(self, other: T) -> T:
        """Merge another object into this one."""
        ...

# Protocol for objects that can be compared for similarity
@runtime_checkable
class SimilarityComparable(Protocol):
    """Protocol for objects that can be compared for similarity."""
    
    def similarity(self, other: Any) -> float:
        """Calculate similarity score with another object."""
        ...

# Protocol for objects that can be converted to embeddings
@runtime_checkable
class Embeddable(Protocol):
    """Protocol for objects that can be converted to embeddings."""
    
    def to_embedding(self) -> List[float]:
        """Convert object to embedding vector."""
        ...

# Protocol for objects that can be chunked
@runtime_checkable
class Chunkable(Protocol[T]):
    """Protocol for objects that can be chunked."""
    
    def chunk(
        self,
        chunk_size: int,
        overlap: int = 0
    ) -> List[T]:
        """Split object into chunks."""
        ... 