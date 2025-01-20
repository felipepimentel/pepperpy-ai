"""Common types and data structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TypedDict, Protocol
from abc import ABC, abstractmethod

from .errors import PepperpyError


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


class PepperpyObject(Protocol):
    """Base protocol for all Pepperpy objects."""
    
    @property
    def name(self) -> str:
        """Get object name."""
        ...


class DictInitializable(Protocol):
    """Protocol for objects that can be initialized from a dictionary."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DictInitializable":
        """Initialize object from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Initialized object
        """
        ...
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary.
        
        Returns:
            Dictionary representation
        """
        ...


class Validatable(Protocol):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> None:
        """Validate object state.
        
        Raises:
            ValueError: If validation fails
        """
        ...


class ServiceError(PepperpyError):
    """Service error."""
    pass


class RESTService(Protocol):
    """REST service interface."""
    
    async def handle_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Handle REST request.
        
        Args:
            method: HTTP method
            path: Request path
            data: Optional request data
            headers: Optional request headers
            
        Returns:
            Response data
            
        Raises:
            ServiceError: If request handling fails
            NotImplementedError: If not implemented by concrete class
        """
        raise NotImplementedError


class WebSocketService(Protocol):
    """WebSocket service interface."""
    
    async def handle_message(
        self,
        message: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle WebSocket message.
        
        Args:
            message: Message data
            context: Optional message context
            
        Returns:
            Response data
            
        Raises:
            ServiceError: If message handling fails
            NotImplementedError: If not implemented by concrete class
        """
        raise NotImplementedError


__all__ = [
    "Message",
    "Document",
    "RAGSearchKwargs",
    "PepperpyObject",
    "DictInitializable",
    "Validatable",
    "ServiceError",
    "RESTService",
    "WebSocketService",
]
