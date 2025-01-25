"""Base memory system module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.core.utils.errors import PepperpyError


class MemoryError(PepperpyError):
    """Memory system error."""
    pass


class MemorySystem(ABC):
    """Base memory system class.
    
    This class defines the interface for memory systems in Pepperpy.
    All memory systems should inherit from this class.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize memory system.
        
        Args:
            name: Memory system name
            config: Optional configuration dictionary
        """
        self.name = name
        self._config = config or {}
        self._is_initialized = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get memory system configuration."""
        return self._config
    
    @property
    def is_initialized(self) -> bool:
        """Check if memory system is initialized."""
        return self._is_initialized
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize memory system.
        
        This method should be called before using the memory system.
        """
        self._is_initialized = True
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up memory system.
        
        This method should be called when the memory system is no longer needed.
        """
        self._is_initialized = False
    
    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store value in memory.
        
        Args:
            key: Key to store value under
            value: Value to store
            
        Raises:
            MemoryError: If storing fails
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from memory.
        
        Args:
            key: Key to retrieve value for
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            MemoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from memory.
        
        Args:
            key: Key to delete value for
            
        Raises:
            MemoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from memory.
        
        Raises:
            MemoryError: If clearing fails
        """
        pass
    
    @abstractmethod
    async def list_keys(self) -> List[str]:
        """List all keys in memory.
        
        Returns:
            List of keys
            
        Raises:
            MemoryError: If listing fails
        """
        pass 