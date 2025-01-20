"""Base memory interfaces and abstractions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, runtime_checkable

from ..core.lifecycle import Lifecycle
from ..models.types import Message


T = TypeVar("T")


@runtime_checkable
class MemoryBackend(Protocol):
    """Memory backend interface."""
    
    async def initialize(self) -> None:
        """Initialize backend."""
        ...
        
    async def cleanup(self) -> None:
        """Clean up backend."""
        ...
        
    async def store(self, key: str, value: Any) -> None:
        """Store value.
        
        Args:
            key: Storage key
            value: Value to store
        """
        ...
        
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
        """
        ...
        
    async def delete(self, key: str) -> None:
        """Delete value.
        
        Args:
            key: Storage key
        """
        ...
        
    async def clear(self) -> None:
        """Clear all values."""
        ...


class BaseMemory(Lifecycle, ABC):
    """Base memory class."""
    
    def __init__(
        self,
        name: str,
        backend: MemoryBackend,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory.
        
        Args:
            name: Memory name
            backend: Memory backend
            config: Optional memory configuration
        """
        super().__init__(name)
        self._backend = backend
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return memory configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize memory."""
        await self._backend.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up memory."""
        await self._backend.cleanup()
        
    @abstractmethod
    async def add_message(self, message: Message) -> None:
        """Add message to memory.
        
        Args:
            message: Message to add
        """
        pass
        
    @abstractmethod
    async def get_messages(
        self,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            limit: Optional message limit
            filters: Optional message filters
            
        Returns:
            List of messages
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear memory."""
        pass
        
    def validate(self) -> None:
        """Validate memory state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Memory name cannot be empty")
            
        if not self._backend:
            raise ValueError("Memory backend not provided") 