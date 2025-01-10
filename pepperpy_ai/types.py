"""Common type definitions."""

from enum import Enum
from typing import (
    Any,
    TypeVar,
    Protocol,
    runtime_checkable,
    AsyncGenerator,
    Optional,
    TypedDict,
)
from dataclasses import dataclass
from datetime import datetime

# Type aliases for common types
JsonDict = dict[str, Any]
JsonList = list[Any]
ProviderResponse = dict[str, Any]

class BaseConfig(TypedDict):
    """Base configuration type."""
    name: str
    version: str
    enabled: bool

class BaseModel(TypedDict):
    """Base model type."""
    id: str
    created_at: str
    updated_at: str

# Generic type variables with constraints
ConfigT = TypeVar("ConfigT", bound=BaseConfig)
ModelT = TypeVar("ModelT", bound=BaseModel)

class MessageRole(str, Enum):
    """Message role types."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

@runtime_checkable
class Serializable(Protocol):
    """Protocol for serializable objects."""
    def to_dict(self) -> JsonDict: ...
    @classmethod
    def from_dict(cls, data: JsonDict) -> "Serializable": ...

@dataclass
class AIMessage:
    """AI message type."""
    role: MessageRole
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[JsonDict] = None

    def __post_init__(self) -> None:
        """Post initialization processing."""
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> JsonDict:
        """Convert to dictionary."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "AIMessage":
        """Create from dictionary.
        
        Args:
            data: Dictionary containing message data
            
        Returns:
            AIMessage instance
            
        Raises:
            ValidationError: If required fields are missing
        """
        try:
            return cls(
                role=data["role"],
                content=data["content"],
                timestamp=datetime.fromisoformat(
                    data.get("timestamp", datetime.now().isoformat())
                ),
                metadata=data.get("metadata", {})
            )
        except KeyError as e:
            from .exceptions import ValidationError
            raise ValidationError(
                f"Missing required field: {e}",
                field=str(e),
                value=None
            )

@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI providers."""
    async def complete(self, prompt: str) -> AIMessage: ...
    async def stream(self, prompt: str) -> AsyncGenerator[AIMessage, None]: ...
    async def get_embedding(self, text: str) -> list[float]: ...
    async def validate_response(self, response: ProviderResponse) -> bool: ...
