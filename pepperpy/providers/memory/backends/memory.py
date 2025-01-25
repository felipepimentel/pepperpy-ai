"""In-memory backend implementation."""

import copy
import json
import logging
from typing import Any, Dict, Optional

from ...common.errors import PepperpyError
from ..base import MemoryBackend


logger = logging.getLogger(__name__)


class MemoryError(PepperpyError):
    """Memory error."""
    pass


class InMemoryBackend(MemoryBackend):
    """In-memory backend implementation."""
    
    def __init__(self) -> None:
        """Initialize in-memory backend."""
        self._storage: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize backend."""
        pass
        
    async def cleanup(self) -> None:
        """Clean up backend."""
        self._storage.clear()
        
    async def store(self, key: str, value: Any) -> None:
        """Store value.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            MemoryError: If value cannot be stored
        """
        try:
            # Make a deep copy to prevent mutations
            self._storage[key] = copy.deepcopy(value)
            
        except Exception as e:
            raise MemoryError(f"Failed to store value: {e}") from e
            
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            MemoryError: If value cannot be retrieved
        """
        try:
            value = self._storage.get(key)
            if value is None:
                return None
                
            # Make a deep copy to prevent mutations
            return copy.deepcopy(value)
            
        except Exception as e:
            raise MemoryError(f"Failed to retrieve value: {e}") from e
            
    async def delete(self, key: str) -> None:
        """Delete value.
        
        Args:
            key: Storage key
            
        Raises:
            MemoryError: If value cannot be deleted
        """
        try:
            self._storage.pop(key, None)
            
        except Exception as e:
            raise MemoryError(f"Failed to delete value: {e}") from e
            
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            MemoryError: If values cannot be cleared
        """
        try:
            self._storage.clear()
            
        except Exception as e:
            raise MemoryError(f"Failed to clear values: {e}") from e 