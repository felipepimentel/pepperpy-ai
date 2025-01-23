"""Common types and data structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TypedDict

from .errors import PepperpyError
from ..interfaces import (
    PepperpyObject,
    DictInitializable,
    Validatable,
    RESTService,
    WebSocketService,
)


@dataclass
class Message:
    """Message class for model interactions."""
    
    content: str
    role: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.role}: {self.content}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Message instance
        """
        return cls(
            content=data["content"],
            role=data["role"],
            metadata=data.get("metadata", {}),
        )


class Document(TypedDict, total=False):
    """Document type."""
    content: str
    metadata: Dict[str, str | int | float | bool | None]


class RAGSearchKwargs(TypedDict, total=False):
    """RAG search keyword arguments."""
    model: str
    temperature: float
    max_tokens: int
    top_k: int
    min_score: float


class ServiceError(PepperpyError):
    """Service error."""
    pass


__all__ = [
    "Message",
    "Document",
    "RAGSearchKwargs",
    "ServiceError",
    # Re-exported from interfaces
    "PepperpyObject",
    "DictInitializable",
    "Validatable",
    "RESTService",
    "WebSocketService",
]
